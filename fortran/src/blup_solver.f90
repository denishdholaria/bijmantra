!===============================================================================
! BLUP/GBLUP Solver Module
! Best Linear Unbiased Prediction for Breeding Value Estimation
!
! Bijmantra Plant Breeding Platform
! Aerospace-Grade Numerical Precision
!
! Author: Bijmantra Team
! License: MIT
!===============================================================================

module blup_solver
    use iso_c_binding
    use iso_fortran_env, only: real64, int32
    implicit none
    
    private
    public :: compute_blup, compute_gblup, solve_mme
    
    ! Precision constants
    integer, parameter :: dp = real64
    real(dp), parameter :: TOLERANCE = 1.0d-10
    integer, parameter :: MAX_ITERATIONS = 1000
    
contains

    !---------------------------------------------------------------------------
    ! Compute BLUP (Best Linear Unbiased Prediction)
    ! Solves the Mixed Model Equations: [X'R⁻¹X  X'R⁻¹Z] [β]   [X'R⁻¹y]
    !                                   [Z'R⁻¹X  Z'R⁻¹Z+G⁻¹] [u] = [Z'R⁻¹y]
    !
    ! Parameters:
    !   y          - Phenotypic observations (n x 1)
    !   X          - Fixed effects design matrix (n x p)
    !   Z          - Random effects design matrix (n x q)
    !   A_inv      - Inverse of relationship matrix (q x q)
    !   var_a      - Additive genetic variance
    !   var_e      - Residual variance
    !   beta       - Output: Fixed effects estimates (p x 1)
    !   u          - Output: Random effects (breeding values) (q x 1)
    !   n, p, q    - Dimensions
    !
    ! Returns: 0 on success, error code otherwise
    !---------------------------------------------------------------------------
    function compute_blup(y, X, Z, A_inv, var_a, var_e, beta, u, n, p, q) &
        result(status) bind(C, name="compute_blup")
        
        integer(c_int), intent(in), value :: n, p, q
        real(c_double), intent(in) :: y(n)
        real(c_double), intent(in) :: X(n, p)
        real(c_double), intent(in) :: Z(n, q)
        real(c_double), intent(in) :: A_inv(q, q)
        real(c_double), intent(in), value :: var_a, var_e
        real(c_double), intent(out) :: beta(p)
        real(c_double), intent(out) :: u(q)
        integer(c_int) :: status
        
        ! Local variables
        real(dp), allocatable :: C(:,:), rhs(:), solution(:)
        real(dp) :: lambda
        integer :: i, j, info
        integer :: lda, ldb, nrhs
        integer, allocatable :: ipiv(:)
        
        ! Calculate lambda (variance ratio)
        lambda = var_e / var_a
        
        ! Allocate coefficient matrix and RHS
        allocate(C(p+q, p+q), rhs(p+q), solution(p+q), ipiv(p+q))
        
        ! Build coefficient matrix
        ! Upper left: X'X
        C(1:p, 1:p) = matmul(transpose(X), X)
        
        ! Upper right: X'Z
        C(1:p, p+1:p+q) = matmul(transpose(X), Z)
        
        ! Lower left: Z'X
        C(p+1:p+q, 1:p) = matmul(transpose(Z), X)
        
        ! Lower right: Z'Z + λA⁻¹
        C(p+1:p+q, p+1:p+q) = matmul(transpose(Z), Z) + lambda * A_inv
        
        ! Build RHS vector
        rhs(1:p) = matmul(transpose(X), y)
        rhs(p+1:p+q) = matmul(transpose(Z), y)
        
        ! Solve using LAPACK (DGESV)
        solution = rhs
        lda = p + q
        ldb = p + q
        nrhs = 1
        
        call dgesv(p+q, nrhs, C, lda, ipiv, solution, ldb, info)
        
        if (info /= 0) then
            status = -1
            deallocate(C, rhs, solution, ipiv)
            return
        end if
        
        ! Extract solutions
        beta = solution(1:p)
        u = solution(p+1:p+q)
        
        status = 0
        deallocate(C, rhs, solution, ipiv)
        
    end function compute_blup

    !---------------------------------------------------------------------------
    ! Compute GBLUP (Genomic BLUP)
    ! Uses genomic relationship matrix G instead of pedigree-based A
    !
    ! Parameters:
    !   genotypes  - Marker genotype matrix (n x m), coded as 0, 1, 2
    !   phenotypes - Phenotypic observations (n x 1)
    !   gebv       - Output: Genomic Estimated Breeding Values (n x 1)
    !   n          - Number of individuals
    !   m          - Number of markers
    !   h2         - Heritability estimate
    !
    ! Returns: 0 on success, error code otherwise
    !---------------------------------------------------------------------------
    function compute_gblup(genotypes, phenotypes, gebv, n, m, h2) &
        result(status) bind(C, name="compute_gblup")
        
        integer(c_int), intent(in), value :: n, m
        real(c_double), intent(in) :: genotypes(n, m)
        real(c_double), intent(in) :: phenotypes(n)
        real(c_double), intent(out) :: gebv(n)
        real(c_double), intent(in), value :: h2
        integer(c_int) :: status
        
        ! Local variables
        real(dp), allocatable :: Z(:,:), G(:,:), G_inv(:,:)
        real(dp), allocatable :: p_freq(:), scale_factor
        real(dp), allocatable :: C(:,:), rhs(:), solution(:)
        real(dp) :: lambda, mean_pheno
        integer :: i, j, info
        integer, allocatable :: ipiv(:)
        
        ! Allocate arrays
        allocate(Z(n, m), G(n, n), G_inv(n, n), p_freq(m))
        allocate(C(n+1, n+1), rhs(n+1), solution(n+1), ipiv(n+1))
        
        ! Calculate allele frequencies
        do j = 1, m
            p_freq(j) = sum(genotypes(:, j)) / (2.0_dp * n)
        end do
        
        ! Center and scale genotype matrix (VanRaden Method 1)
        do j = 1, m
            Z(:, j) = genotypes(:, j) - 2.0_dp * p_freq(j)
        end do
        
        ! Calculate scaling factor
        scale_factor = 2.0_dp * sum(p_freq * (1.0_dp - p_freq))
        
        ! Compute G matrix: G = ZZ'/scale_factor
        G = matmul(Z, transpose(Z)) / scale_factor
        
        ! Add small value to diagonal for numerical stability
        do i = 1, n
            G(i, i) = G(i, i) + 0.001_dp
        end do
        
        ! Invert G matrix
        G_inv = G
        call matrix_inverse(G_inv, n, info)
        
        if (info /= 0) then
            status = -1
            deallocate(Z, G, G_inv, p_freq, C, rhs, solution, ipiv)
            return
        end if
        
        ! Calculate lambda
        lambda = (1.0_dp - h2) / h2
        
        ! Build MME coefficient matrix
        ! [1'1    1'    ] [μ]   [1'y]
        ! [1      I+λG⁻¹] [u] = [y  ]
        
        C(1, 1) = real(n, dp)
        C(1, 2:n+1) = 1.0_dp
        C(2:n+1, 1) = 1.0_dp
        
        do i = 1, n
            do j = 1, n
                if (i == j) then
                    C(i+1, j+1) = 1.0_dp + lambda * G_inv(i, j)
                else
                    C(i+1, j+1) = lambda * G_inv(i, j)
                end if
            end do
        end do
        
        ! Build RHS
        rhs(1) = sum(phenotypes)
        rhs(2:n+1) = phenotypes
        
        ! Solve system
        solution = rhs
        call dgesv(n+1, 1, C, n+1, ipiv, solution, n+1, info)
        
        if (info /= 0) then
            status = -2
            deallocate(Z, G, G_inv, p_freq, C, rhs, solution, ipiv)
            return
        end if
        
        ! Extract GEBVs
        gebv = solution(2:n+1)
        
        status = 0
        deallocate(Z, G, G_inv, p_freq, C, rhs, solution, ipiv)
        
    end function compute_gblup

    !---------------------------------------------------------------------------
    ! Solve Mixed Model Equations using Iterative Method (PCG)
    ! For large-scale problems where direct methods are too expensive
    !
    ! Parameters:
    !   C          - Coefficient matrix (dim x dim)
    !   rhs        - Right-hand side vector (dim x 1)
    !   solution   - Output: Solution vector (dim x 1)
    !   dim        - Dimension of the system
    !   tol        - Convergence tolerance
    !   max_iter   - Maximum iterations
    !
    ! Returns: Number of iterations, or negative on error
    !---------------------------------------------------------------------------
    function solve_mme(C, rhs, solution, dim, tol, max_iter) &
        result(iterations) bind(C, name="solve_mme")
        
        integer(c_int), intent(in), value :: dim, max_iter
        real(c_double), intent(in) :: C(dim, dim)
        real(c_double), intent(in) :: rhs(dim)
        real(c_double), intent(inout) :: solution(dim)
        real(c_double), intent(in), value :: tol
        integer(c_int) :: iterations
        
        ! Local variables for PCG
        real(dp), allocatable :: r(:), p(:), Ap(:), z(:), M_inv(:)
        real(dp) :: alpha, beta_cg, rz_old, rz_new, pAp
        real(dp) :: residual_norm
        integer :: iter
        
        allocate(r(dim), p(dim), Ap(dim), z(dim), M_inv(dim))
        
        ! Diagonal preconditioner
        do iter = 1, dim
            if (abs(C(iter, iter)) > 1.0d-15) then
                M_inv(iter) = 1.0_dp / C(iter, iter)
            else
                M_inv(iter) = 1.0_dp
            end if
        end do
        
        ! Initial residual: r = rhs - C*x
        r = rhs - matmul(C, solution)
        
        ! Apply preconditioner: z = M⁻¹r
        z = M_inv * r
        
        ! Initial search direction
        p = z
        
        ! Initial rz product
        rz_old = dot_product(r, z)
        
        ! PCG iteration
        do iter = 1, max_iter
            ! Ap = C * p
            Ap = matmul(C, p)
            
            ! pAp = p' * Ap
            pAp = dot_product(p, Ap)
            
            if (abs(pAp) < 1.0d-15) then
                iterations = -1
                deallocate(r, p, Ap, z, M_inv)
                return
            end if
            
            ! Step size
            alpha = rz_old / pAp
            
            ! Update solution
            solution = solution + alpha * p
            
            ! Update residual
            r = r - alpha * Ap
            
            ! Check convergence
            residual_norm = sqrt(dot_product(r, r))
            if (residual_norm < tol) then
                iterations = iter
                deallocate(r, p, Ap, z, M_inv)
                return
            end if
            
            ! Apply preconditioner
            z = M_inv * r
            
            ! New rz product
            rz_new = dot_product(r, z)
            
            ! Update search direction
            beta_cg = rz_new / rz_old
            p = z + beta_cg * p
            
            rz_old = rz_new
        end do
        
        ! Did not converge
        iterations = -max_iter
        deallocate(r, p, Ap, z, M_inv)
        
    end function solve_mme

    !---------------------------------------------------------------------------
    ! Matrix Inverse using LAPACK (DGETRF + DGETRI)
    !---------------------------------------------------------------------------
    subroutine matrix_inverse(A, n, info)
        integer, intent(in) :: n
        real(dp), intent(inout) :: A(n, n)
        integer, intent(out) :: info
        
        integer, allocatable :: ipiv(:)
        real(dp), allocatable :: work(:)
        integer :: lwork
        
        allocate(ipiv(n), work(n*n))
        lwork = n * n
        
        ! LU factorization
        call dgetrf(n, n, A, n, ipiv, info)
        if (info /= 0) then
            deallocate(ipiv, work)
            return
        end if
        
        ! Compute inverse
        call dgetri(n, A, n, ipiv, work, lwork, info)
        
        deallocate(ipiv, work)
        
    end subroutine matrix_inverse

end module blup_solver
