!===============================================================================
! Kinship Matrix Module
! Genomic Relationship Matrix Computation
!
! Bijmantra Plant Breeding Platform
! Aerospace-Grade Numerical Precision
!
! Methods:
! - VanRaden Method 1 (2008)
! - VanRaden Method 2 (2008)
! - Yang et al. (2010)
! - Dominance Relationship Matrix
!
! Author: Bijmantra Team
! License: MIT
!===============================================================================

module kinship
    use iso_c_binding
    use iso_fortran_env, only: real64, int32
    implicit none
    
    private
    public :: compute_grm_vanraden1, compute_grm_vanraden2, compute_grm_yang
    public :: compute_dominance_matrix, compute_epistatic_matrix
    
    integer, parameter :: dp = real64
    
contains

    !---------------------------------------------------------------------------
    ! Compute Genomic Relationship Matrix - VanRaden Method 1 (2008)
    ! G = ZZ' / (2 * Σ p_i * (1 - p_i))
    !
    ! Parameters:
    !   genotypes  - Marker matrix (n x m), coded as 0, 1, 2
    !   G          - Output: Genomic relationship matrix (n x n)
    !   n          - Number of individuals
    !   m          - Number of markers
    !
    ! Returns: 0 on success
    !---------------------------------------------------------------------------
    function compute_grm_vanraden1(genotypes, G, n, m) &
        result(status) bind(C, name="compute_grm_vanraden1")
        
        integer(c_int), intent(in), value :: n, m
        real(c_double), intent(in) :: genotypes(n, m)
        real(c_double), intent(out) :: G(n, n)
        integer(c_int) :: status
        
        ! Local variables
        real(dp), allocatable :: Z(:,:), p(:)
        real(dp) :: scale_factor
        integer :: i, j
        
        allocate(Z(n, m), p(m))
        
        ! Calculate allele frequencies
        do j = 1, m
            p(j) = sum(genotypes(:, j)) / (2.0_dp * n)
        end do
        
        ! Center genotype matrix: Z_ij = M_ij - 2p_j
        do j = 1, m
            Z(:, j) = genotypes(:, j) - 2.0_dp * p(j)
        end do
        
        ! Calculate scaling factor: 2 * Σ p_i * (1 - p_i)
        scale_factor = 2.0_dp * sum(p * (1.0_dp - p))
        
        ! Prevent division by zero
        if (scale_factor < 1.0d-10) then
            scale_factor = 1.0_dp
        end if
        
        ! Compute G = ZZ' / scale_factor
        ! Using BLAS DGEMM for efficiency
        call dgemm('N', 'T', n, n, m, 1.0_dp/scale_factor, Z, n, Z, n, 0.0_dp, G, n)
        
        status = 0
        deallocate(Z, p)
        
    end function compute_grm_vanraden1

    !---------------------------------------------------------------------------
    ! Compute Genomic Relationship Matrix - VanRaden Method 2 (2008)
    ! G_ij = Σ (M_ik - 2p_k)(M_jk - 2p_k) / (2p_k(1-p_k)) / m
    !
    ! This method weights each marker by its heterozygosity
    !---------------------------------------------------------------------------
    function compute_grm_vanraden2(genotypes, G, n, m) &
        result(status) bind(C, name="compute_grm_vanraden2")
        
        integer(c_int), intent(in), value :: n, m
        real(c_double), intent(in) :: genotypes(n, m)
        real(c_double), intent(out) :: G(n, n)
        integer(c_int) :: status
        
        ! Local variables
        real(dp), allocatable :: Z(:,:), p(:), weights(:)
        real(dp) :: het
        integer :: i, j, k
        
        allocate(Z(n, m), p(m), weights(m))
        
        ! Calculate allele frequencies and weights
        do j = 1, m
            p(j) = sum(genotypes(:, j)) / (2.0_dp * n)
            het = 2.0_dp * p(j) * (1.0_dp - p(j))
            if (het > 1.0d-10) then
                weights(j) = 1.0_dp / het
            else
                weights(j) = 0.0_dp
            end if
        end do
        
        ! Center and weight genotype matrix
        do j = 1, m
            Z(:, j) = (genotypes(:, j) - 2.0_dp * p(j)) * sqrt(weights(j))
        end do
        
        ! Compute G = ZZ' / m
        call dgemm('N', 'T', n, n, m, 1.0_dp/real(m, dp), Z, n, Z, n, 0.0_dp, G, n)
        
        status = 0
        deallocate(Z, p, weights)
        
    end function compute_grm_vanraden2

    !---------------------------------------------------------------------------
    ! Compute Genomic Relationship Matrix - Yang et al. (2010)
    ! G_ij = (1/m) * Σ (M_ik - 2p_k)(M_jk - 2p_k) / (2p_k(1-p_k))
    !
    ! Similar to VanRaden Method 2 but with different normalization
    !---------------------------------------------------------------------------
    function compute_grm_yang(genotypes, G, n, m) &
        result(status) bind(C, name="compute_grm_yang")
        
        integer(c_int), intent(in), value :: n, m
        real(c_double), intent(in) :: genotypes(n, m)
        real(c_double), intent(out) :: G(n, n)
        integer(c_int) :: status
        
        ! Local variables
        real(dp), allocatable :: p(:)
        real(dp) :: het, z_i, z_j
        integer :: i, j, k
        integer :: valid_markers
        
        allocate(p(m))
        
        ! Calculate allele frequencies
        do k = 1, m
            p(k) = sum(genotypes(:, k)) / (2.0_dp * n)
        end do
        
        ! Initialize G
        G = 0.0_dp
        valid_markers = 0
        
        ! Compute G element by element (more memory efficient for large m)
        do k = 1, m
            het = 2.0_dp * p(k) * (1.0_dp - p(k))
            if (het < 1.0d-10) cycle
            
            valid_markers = valid_markers + 1
            
            do i = 1, n
                z_i = genotypes(i, k) - 2.0_dp * p(k)
                do j = i, n
                    z_j = genotypes(j, k) - 2.0_dp * p(k)
                    G(i, j) = G(i, j) + (z_i * z_j) / het
                end do
            end do
        end do
        
        ! Normalize and symmetrize
        if (valid_markers > 0) then
            G = G / real(valid_markers, dp)
        end if
        
        ! Fill lower triangle
        do i = 2, n
            do j = 1, i-1
                G(i, j) = G(j, i)
            end do
        end do
        
        status = 0
        deallocate(p)
        
    end function compute_grm_yang

    !---------------------------------------------------------------------------
    ! Compute Dominance Relationship Matrix
    ! D_ij = Σ W_ik * W_jk / Σ (2p_k(1-p_k))²
    ! where W_ik = -2p_k² if M_ik=0, 2p_k(1-p_k) if M_ik=1, -2(1-p_k)² if M_ik=2
    !---------------------------------------------------------------------------
    function compute_dominance_matrix(genotypes, D, n, m) &
        result(status) bind(C, name="compute_dominance_matrix")
        
        integer(c_int), intent(in), value :: n, m
        real(c_double), intent(in) :: genotypes(n, m)
        real(c_double), intent(out) :: D(n, n)
        integer(c_int) :: status
        
        ! Local variables
        real(dp), allocatable :: W(:,:), p(:)
        real(dp) :: scale_factor, het, q
        integer :: i, j, k
        
        allocate(W(n, m), p(m))
        
        ! Calculate allele frequencies
        do k = 1, m
            p(k) = sum(genotypes(:, k)) / (2.0_dp * n)
        end do
        
        ! Compute dominance deviations
        scale_factor = 0.0_dp
        do k = 1, m
            q = 1.0_dp - p(k)
            het = 2.0_dp * p(k) * q
            
            if (het < 1.0d-10) then
                W(:, k) = 0.0_dp
                cycle
            end if
            
            scale_factor = scale_factor + het * het
            
            do i = 1, n
                if (abs(genotypes(i, k)) < 0.5_dp) then
                    ! Genotype 0 (aa)
                    W(i, k) = -2.0_dp * p(k) * p(k)
                else if (abs(genotypes(i, k) - 1.0_dp) < 0.5_dp) then
                    ! Genotype 1 (Aa)
                    W(i, k) = het
                else
                    ! Genotype 2 (AA)
                    W(i, k) = -2.0_dp * q * q
                end if
            end do
        end do
        
        ! Prevent division by zero
        if (scale_factor < 1.0d-10) then
            scale_factor = 1.0_dp
        end if
        
        ! Compute D = WW' / scale_factor
        call dgemm('N', 'T', n, n, m, 1.0_dp/scale_factor, W, n, W, n, 0.0_dp, D, n)
        
        status = 0
        deallocate(W, p)
        
    end function compute_dominance_matrix

    !---------------------------------------------------------------------------
    ! Compute Epistatic (Additive x Additive) Relationship Matrix
    ! E = G ⊙ G (Hadamard product of additive GRM with itself)
    !---------------------------------------------------------------------------
    function compute_epistatic_matrix(G, E, n) &
        result(status) bind(C, name="compute_epistatic_matrix")
        
        integer(c_int), intent(in), value :: n
        real(c_double), intent(in) :: G(n, n)
        real(c_double), intent(out) :: E(n, n)
        integer(c_int) :: status
        
        integer :: i, j
        
        ! Hadamard product
        do j = 1, n
            do i = 1, n
                E(i, j) = G(i, j) * G(i, j)
            end do
        end do
        
        status = 0
        
    end function compute_epistatic_matrix

end module kinship
