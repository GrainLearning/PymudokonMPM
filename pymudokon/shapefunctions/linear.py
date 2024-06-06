"""Module for containing the linear shape functions."""

from functools import partial
from typing import Tuple

import jax
import jax.numpy as jnp
from flax import struct
from jax import Array
from typing_extensions import Self

from ..core.nodes import Nodes
from ..core.particles import Particles
from .shapefunction import ShapeFunction


@struct.dataclass
class LinearShapeFunction(ShapeFunction):
    """Linear shape functions for the particle-node interactions."""

    @classmethod
    def create(cls: Self, num_particles: jnp.int32, dim: jnp.int16) -> Self:
        """Initializes the state of the linear shape functions.

        Args:
            cls (Self): Self type reference
            num_particles (jnp.int32): Number of particles
            dim (jnp.int16): Dimension of the problem

        Returns: ShapeFunction: Initialized shape function and interactions state.
        """
        # Generate the stencil based on the dimension
        if dim == 1:
            stencil = jnp.array([[0.0], [1.0]])
        if dim == 2:
            stencil = jnp.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
        if dim == 3:
            stencil = jnp.array(
                [[0, 0, 0], [0, 0, 1], [1, 0, 0], [1, 0, 1], [0, 1, 0], [0, 1, 1], [1, 1, 0], [1, 1, 1]]
            )

        stencil_size = stencil.shape[0]

        return cls(
            intr_hashes=jnp.zeros((num_particles * stencil_size), dtype=jnp.int32),
            intr_shapef=jnp.zeros((num_particles, stencil_size), dtype=jnp.float32),
            intr_shapef_grad=jnp.zeros((num_particles, stencil_size, dim), dtype=jnp.float32),
            stencil=stencil,
        )

    @jax.jit
    def calculate_shapefunction(self: Self, nodes: Nodes, particles: Particles) -> Self:
        """Top level function to calculate the shape functions. Assumes `get_interactions` has been called.

        Args:
            self (LinearShapeFunction):
                Shape function at previous state
            nodes (Nodes):
                Nodes state containing grid size and inv_node_spacing
            particles (Particles):
                Particles state containing particle positions

        Returns:>
            LinearShapeFunction: Updated shape function state for the particle and node pairs.
        """
        # Solution procedure:
        _, dim = self.stencil.shape

        # 1. Calculate the particle-node pair interactions
        # see `ShapeFunction class` for more details
        intr_dist, intr_hashes = self.vmap_interactions(
            particles.positions,
            nodes.origin,
            nodes.inv_node_spacing,
            nodes.grid_size,
        )

        # 2. Reshape arrays to be batched
        intr_dist = intr_dist.reshape(-1, dim, 1)
        intr_hashes = intr_hashes.reshape(-1)

        # 3. Calculate the shape functions
        intr_shapef = self.vmap_linear_shapefunction(
            intr_dist, nodes.inv_node_spacing
        )

        # 4. Calculate the shape function gradients
        intr_shapef_grad = jax.grad(self.vmap_linear_shapefunction)(
            intr_dist, nodes.inv_node_spacing
        )

        return self.replace(
            intr_shapef=intr_shapef,
            intr_shapef_grad=intr_shapef_grad)

    @partial(jax.vmap, in_axes=(None,0, None))
    def vmap_linear_shapefunction(
        self: Self,
        intr_dist: Array,
        inv_node_spacing: jnp.float32,
    ) -> Tuple[Array, Array]:
        """Vectorized linear shape function calculation.

        Calculate the shape function, and then its gradient

        Args:
            intr_dist (Array):
                Particle-node pair interactions distance.
            inv_node_spacing (jnp.float32):
                Inverse node spacing.

        Returns:
            Tuple[Array, Array]:
                Shape function and its gradient.
        """
        num_interactions, dim, _ = intr_dist.shape

        abs_intr_dist = jnp.abs(intr_dist)
        basis = jnp.where(abs_intr_dist < 1.0, 1.0 - abs_intr_dist, 0.0)

        intr_shapef = jax.lax.switch(
            dim-1,
            lambda _: basis, #1D
            lambda _: jnp.expand_dims(basis[0, :] * basis[1, :], axis=1), #2D
            lambda _:  jnp.expand_dims(basis[0, :] * basis[1, :] * basis[2, :], axis=1) #3D
        )

        # shapes of returned array are
        # (num_particles*stencil_size, 1, 1)
        return intr_shapef
