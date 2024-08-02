"""Module for containing the cubic shape functions.

References:
    - De Vaucorbeil, Alban, et al. 'Material point method after 25 years: theory,
    implementation, and applications.'
"""

from functools import partial
from typing import Tuple
from typing_extensions import Self

import chex
import jax
import jax.numpy as jnp
from jax import Array

from .shapefunctions import ShapeFunction


@chex.dataclass(mappable_dataclass=False, frozen=True)
class CubicShapeFunction(ShapeFunction):
    """Cubic B-spline shape functions for the particle-node interactions."""

    @classmethod
    def create(cls: Self, num_particles: jax.numpy.int32, dim: jax.numpy.int16) -> Self:
        """Initializes Cubic B-splines.

        It is recommended that each background cell is populated by
        2 (1D), 4 (2D), 8 (3D) material points. The optimal integration points are
        at 0.2113, 0.7887 determined by Gauss quadrature rule.

        Args:
            cls (Self):
                self type reference
            num_particles (jax.numpy.int32):
                Number of particles
            dim (jax.numpy.int16):
                Dimension of the problem

        Returns:
            ShapeFunction:
                Container for shape functions and gradients
        """
        if dim == 1:
            stencil = jax.numpy.array([[-1], [0], [1], [2]])
        if dim == 2:
            stencil = jax.numpy.array(
                [
                    [-1, -1],
                    [0, -1],
                    [1, -1],
                    [2, -1],
                    [-1, 0],
                    [0, 0],
                    [1, 0],
                    [2, 0],
                    [-1, 1],
                    [0, 1],
                    [1, 1],
                    [2, 1],
                    [-1, 2],
                    [0, 2],
                    [1, 2],
                    [2, 2],
                ]
            )

        if dim == 3:
            stencil = jax.numpy.array(
                [
                    [-1, -1, -1],
                    [-1, -1, 0],
                    [-1, -1, 1],
                    [-1, -1, 2],
                    [0, -1, -1],
                    [0, -1, 0],
                    [0, -1, 1],
                    [0, -1, 2],
                    [1, -1, -1],
                    [1, -1, 0],
                    [1, -1, 1],
                    [1, -1, 2],
                    [2, -1, -1],
                    [2, -1, 0],
                    [2, -1, 1],
                    [2, -1, 2],
                    [-1, 0, -1],
                    [-1, 0, 0],
                    [-1, 0, 1],
                    [-1, 0, 2],
                    [0, 0, -1],
                    [0, 0, 0],
                    [0, 0, 1],
                    [0, 0, 2],
                    [1, 0, -1],
                    [1, 0, 0],
                    [1, 0, 1],
                    [1, 0, 2],
                    [2, 0, -1],
                    [2, 0, 0],
                    [2, 0, 1],
                    [2, 0, 2],
                    [-1, 1, -1],
                    [-1, 1, 0],
                    [-1, 1, 1],
                    [-1, 1, 2],
                    [0, 1, -1],
                    [0, 1, 0],
                    [0, 1, 1],
                    [0, 1, 2],
                    [1, 1, -1],
                    [1, 1, 0],
                    [1, 1, 1],
                    [1, 1, 2],
                    [2, 1, -1],
                    [2, 1, 0],
                    [2, 1, 1],
                    [2, 1, 2],
                    [-1, 2, -1],
                    [-1, 2, 0],
                    [-1, 2, 1],
                    [-1, 2, 2],
                    [0, 2, -1],
                    [0, 2, 0],
                    [0, 2, 1],
                    [0, 2, 2],
                    [1, 2, -1],
                    [1, 2, 0],
                    [1, 2, 1],
                    [1, 2, 2],
                    [2, 2, -1],
                    [2, 2, 0],
                    [2, 2, 1],
                    [2, 2, 2],
                ]
            )

        stencil_size = stencil.shape[0]

        intr_id_stack = jnp.arange(num_particles * stencil_size).astype(jnp.int32)

        return cls(
            intr_id_stack=intr_id_stack,
            intr_hash_stack=jnp.zeros((num_particles * stencil_size), dtype=jnp.int32),
            intr_shapef_stack=jnp.zeros(
                (num_particles * stencil_size), dtype=jnp.float32
            ),
            intr_shapef_grad_stack=jax.numpy.zeros(
                (num_particles * stencil_size, 3), dtype=jnp.float32
            ),
            stencil=stencil,
        )

    def calculate_shapefunction(
        self: Self,
        origin: chex.Array,
        inv_node_spacing: jnp.float32,
        grid_size: chex.Array,
        position_stack: chex.Array,
    ) -> Tuple[Self, Array]:
        """Calculate shape functions and its gradients."""
        stencil_size, dim = self.stencil.shape

        num_particles = position_stack.shape[0]

        intr_id_stack = jnp.arange(num_particles * stencil_size).astype(jnp.int32)

        # Calculate the particle-node pair interactions
        # see `ShapeFunction class` for more details
        intr_dist_stack, intr_hash_stack = self.vmap_intr(
            intr_id_stack, position_stack, origin, inv_node_spacing, grid_size
        )

        intr_shapef_stack, intr_shapef_grad_stack = self.vmap_intr_shp(
            intr_dist_stack, inv_node_spacing
        )

        intr_dist_3d_stack = jnp.pad(
            intr_dist_stack,
            [(0, 0), (0, 3 - dim)],
            mode="constant",
            constant_values=0,
        )

        return self.replace(
            intr_shapef_stack=intr_shapef_stack,
            intr_shapef_grad_stack=intr_shapef_grad_stack,
            intr_id_stack=intr_id_stack,
            intr_hash_stack=intr_hash_stack,
        ), intr_dist_3d_stack

    @partial(jax.vmap, in_axes=(None, 0, None))
    def vmap_intr_shp(
        self,
        intr_dist: Array,
        inv_node_spacing: jax.numpy.float32,
    ) -> Tuple[Array, Array]:
        """Vectorized cubic shape function calculation.

        Calculate the shape function, and then its gradients.

        Args:
            intr_dist (Array):
                Particle-node pair interactions distance.
            intr_species (Array):
                Node type of the background grid. See
                :meth:`pymudokon.core.nodes.Nodes.set_species` for details.
            inv_node_spacing (jax.numpy.float32):
                Inverse node spacing.

        Returns:
            Tuple[Array, Array]:
                Shape function and its gradient.
        """
        spline_branches = [
            middle_splines,  # species 0
            boundary_padding_start_splines,  # species 1
            boundary_padding_end_splines,  # species 2
            boundary_splines,  # species 3
        ]

        basis, dbasis = jax.lax.switch(
            0, spline_branches, (intr_dist, inv_node_spacing)
        )
        intr_shapef = jnp.prod(basis)

        dim = basis.shape[0]
        if dim == 2:
            intr_shapef_grad = jnp.array(
                [
                    dbasis[0] * basis[1],
                    dbasis[1] * basis[0],
                    0.0,
                ]
            )
        elif dim == 3:
            intr_shapef_grad = jnp.array(
                [
                    dbasis[0] * basis[1] * basis[2],
                    dbasis[1] * basis[0] * basis[2],
                    dbasis[2] * basis[0] * basis[1],
                ]
            )
        else:
            intr_shapef_grad = jnp.array([dbasis, 0.0, 0.0])

        return intr_shapef, intr_shapef_grad


def middle_splines(package) -> Tuple[Array, Array]:
    """Splines for inner nodes."""
    intr_dist, inv_node_spacing = package
    conditions = [
        (intr_dist >= 1.0) & (intr_dist < 2.0),
        (intr_dist >= 0.0) & (intr_dist < 1.0),
        (intr_dist >= -1.0) & (intr_dist < 0.0),
        (intr_dist >= -2.0) & (intr_dist < -1.0),
    ]
    # Arrays are evaluated for each condition, is there a better way to do this?
    basis_functions = [
        (lambda x: ((-1.0 / 6.0 * x + 1.0) * x - 2.0) * x + 4.0 / 3.0)(intr_dist),
        (lambda x: (0.5 * x - 1) * x * x + 2.0 / 3.0)(intr_dist),
        (lambda x: (-0.5 * x - 1) * x * x + 2.0 / 3.0)(intr_dist),
        (lambda x: ((1.0 / 6.0 * x + 1.0) * x + 2.0) * x + 4.0 / 3.0)(intr_dist),
    ]

    dbasis_functions = [
        (lambda x, h: h * ((-0.5 * x + 2) * x - 2.0))(intr_dist, inv_node_spacing),
        (lambda x, h: h * (3.0 / 2.0 * x - 2.0) * x)(intr_dist, inv_node_spacing),
        (lambda x, h: h * (-3.0 / 2.0 * x - 2.0) * x)(intr_dist, inv_node_spacing),
        (lambda x, h: h * ((0.5 * x + 2) * x + 2.0))(intr_dist, inv_node_spacing),
    ]
    basis = jax.numpy.select(conditions, basis_functions)
    dbasis = jax.numpy.select(conditions, dbasis_functions)
    return basis, dbasis


def boundary_padding_end_splines(package) -> Tuple[Array, Array]:
    """Splines for nodes at the boundary (end)."""
    intr_dist, inv_node_spacing = package
    conditions = [
        (intr_dist >= 0.0) & (intr_dist < 1.0),
        (intr_dist >= -1.0) & (intr_dist < 0.0),
        (intr_dist >= -2.0) & (intr_dist < -1.0),
    ]

    basis_functions = [
        (lambda x: (1.0 / 3.0 * x - 1.0) * x * x + 2.0 / 3.0)(intr_dist),
        (lambda x: (-0.5 * x - 1) * x * x + 2.0 / 3.0)(intr_dist),
        (lambda x: ((1.0 / 6.0 * x + 1) * x + 2) * x + 4.0 / 3.0)(intr_dist),
    ]

    dbasis_functions = [
        (lambda x, h: h * x * (x - 2))(intr_dist, inv_node_spacing),
        (lambda x, h: h * (-3.0 / 2.0 * x - 2.0) * x)(intr_dist, inv_node_spacing),
        (lambda x, h: h * ((0.5 * x + 2.0) * x + 2.0))(intr_dist, inv_node_spacing),
    ]
    basis = jax.numpy.select(conditions, basis_functions)
    dbasis = jax.numpy.select(conditions, dbasis_functions)
    return basis, dbasis


def boundary_padding_start_splines(package) -> Tuple[Array, Array]:
    """Splines for nodes at the boundary (start)."""
    intr_dist, inv_node_spacing = package
    conditions = [
        (intr_dist >= 1.0) & (intr_dist < 2.0),
        (intr_dist >= 0.0) & (intr_dist < 1.0),
        (intr_dist >= -1.0) & (intr_dist < 0.0),
    ]

    basis_functions = [
        (lambda x: ((-1.0 / 6.0 * x + 1.0) * x - 2.0) * x + 4.0 / 3.0)(intr_dist),
        (lambda x: (0.5 * x - 1) * x * x + 2.0 / 3.0)(intr_dist),
        (lambda x: (-1.0 / 3.0 * x - 1.0) * x * x + 2.0 / 3.0)(intr_dist),
    ]

    dbasis_functions = [
        (lambda x, h: h * ((-0.5 * x + 2) * x - 2.0))(intr_dist, inv_node_spacing),
        (lambda x, h: h * (3.0 / 2.0 * x - 2.0) * x)(intr_dist, inv_node_spacing),
        (lambda x, h: h * (-x - 2) * x)(intr_dist, inv_node_spacing),
    ]
    basis = jax.numpy.select(conditions, basis_functions)
    dbasis = jax.numpy.select(conditions, dbasis_functions)
    return basis, dbasis


def boundary_splines(package) -> Tuple[Array, Array]:
    """Splines at edge of the boundary."""
    intr_dist, inv_node_spacing = package
    conditions = [
        (intr_dist >= 1.0) & (intr_dist < 2.0),
        (intr_dist >= 0.0) & (intr_dist < 1.0),
        (intr_dist >= -1.0) & (intr_dist < 0.0),
        (intr_dist >= -2.0) & (intr_dist < -1.0),
    ]

    basis_functions = [
        (lambda x: ((-1.0 / 6.0 * x + 1.0) * x - 2.0) * x + 4.0 / 3.0)(intr_dist),
        (lambda x: (1.0 / 6.0 * x * x - 1.0) * x + 1.0)(intr_dist),
        (lambda x: (-1.0 / 6.0 * x * x + 1.0) * x + 1.0)(intr_dist),
        (lambda x: ((1.0 / 6.0 * x + 1.0) * x + 2.0) * x + 4.0 / 3.0)(intr_dist),
    ]

    dbasis_functions = [
        (lambda x, h: h * ((-0.5 * x + 2) * x - 2.0))(intr_dist, inv_node_spacing),
        (lambda x, h: h * (0.5 * x * x - 1.0))(intr_dist, inv_node_spacing),
        (lambda x, h: h * (-0.5 * x * x + 1.0))(intr_dist, inv_node_spacing),
        (lambda x, h: h * ((0.5 * x + 2) * x + 2.0))(intr_dist, inv_node_spacing),
    ]
    basis = jax.numpy.select(conditions, basis_functions)
    dbasis = jax.numpy.select(conditions, dbasis_functions)
    return basis, dbasis
