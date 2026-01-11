!===============================================================================
! PCA/SVD Module
! Principal Component Analysis and Singular Value Decomposition
!
! Bijmantra Plant Breeding Platform
! Aerospace-Grade Numerical Precision
!
! Author: Bijmantra Team
! License: MIT
!===============================================================================

module pca_svd
    use iso_c_binding
    use iso_fortran_env, only: real64, int32
    implicit none
    
    private
    public :: compute_pca, compute_svd, truncated_svd
    
    integer, parameter :: dp = real64
    
contains

    !---------------------------------------------------------------------------
    ! Compute PCA (Principal Component Analysis)
    !
    ! Parameters:
    !   X          - Data matrix (n x p), samples in rows
    !   scores     - Output: PC scores (n x k)
    !   loadings   - Output: PC loadings (p x k)
    !   variance   - Output: Variance explained (k)
    !   n, p       - Dimensions
    !   k          - Number of components to retain
    !   center     - Center the data (1=yes, 0=no)
    !   scale      - Scale the data (1=yes, 0=no)
    !
    ! Returns: 0 on success
    !---------------------------------------------------------------------------
    function compute_pca(X, scores, loadings, variance, n, p, k, center, scale) &
        result(status) bind(C, name="compute_pca")
        
        integer(c_int), intent(in), value :: n, p, k, center, scale
        real(c_double), intent(in) :: X(n, p)
        real(c_double), intent(out) :: scores(n, k)
        real(c_double), intent(out) :: loadings(p, k)
        real(c_double), intent(out) :: variance(k)
        integer(c_int) :: status
        
        ! Local variables
        real(dp), allocatable :: X_centered(:,:), means(:), stds(:)
        real(dp), allocatable :: U(:,:), S(:), VT(:,:)
        real(dp) :: total_var
        integer :: i, j, info
        
        allocate(X_centered(n, p), means(p), stds(p))
        allocate(U(n, min(n, p)), S(min(n, p)), VT(min(n, p), p))
        
        ! Copy and optionally center/scale
        X_centered = X
        
        if (center == 1) then
            do j = 1, p
                means(j) = sum(X(:, j)) / real(n, dp)
                X_centered(:, j) = X_centered(:, j) - means(j)
            end do
        end if
        
        if (scale == 1) then
            do j = 1, p
                stds(j) = sqrt(sum(X_centered(:, j)**2) / real(n - 1, dp))
                if (stds(j) > 1.0d-10) then
                    X_centered(:, j) = X_centered(:, j) / stds(j)
                end if
            end do
        end if
        
        ! Compute SVD
        call compute_svd_internal(X_centered, U, S, VT, n, p, info)
        
        if (info /= 0) then
            status = -1
            deallocate(X_centered, means, stds, U, S, VT)
            return
        end if
        
        ! Extract top k components
        scores(:, 1:k) = U(:, 1:k)
        do i = 1, k
            scores(:, i) = scores(:, i) * S(i)
        end do
        
        loadings = transpose(VT(1:k, :))
        
        ! Compute variance explained
        total_var = sum(S**2)
        do i = 1, k
            variance(i) = S(i)**2 / total_var
        end do
        
        status = 0
        deallocate(X_centered, means, stds, U, S, VT)
        
    end function compute_pca

    !---------------------------------------------------------------------------
    ! Compute full SVD using LAPACK
    !---------------------------------------------------------------------------
    function compute_svd(A, U, S, VT, m, n) &
        result(status) bind(C, name="compute_svd")
        
        integer(c_int), intent(in), value :: m, n
        real(c_double), intent(in) :: A(m, n)
        real(c_double), intent(out) :: U(m, min(m, n))
        real(c_double), intent(out) :: S(min(m, n))
        real(c_double), intent(out) :: VT(min(m, n), n)
        integer(c_int) :: status
        
        integer :: info
        
        call compute_svd_internal(A, U, S, VT, m, n, info)
        status = info
        
    end function compute_svd

    !---------------------------------------------------------------------------
    ! Internal SVD computation using LAPACK DGESVD
    !---------------------------------------------------------------------------
    subroutine compute_svd_internal(A, U, S, VT, m, n, info)
        integer, intent(in) :: m, n
        real(dp), intent(in) :: A(m, n)
        real(dp), intent(out) :: U(m, min(m, n))
        real(dp), intent(out) :: S(min(m, n))
        real(dp), intent(out) :: VT(min(m, n), n)
        integer, intent(out) :: info
        
        real(dp), allocatable :: A_copy(:,:), work(:)
        integer :: lwork, k
        
        k = min(m, n)
        allocate(A_copy(m, n))
        A_copy = A
        
        ! Query optimal workspace
        lwork = -1
        allocate(work(1))
        call dgesvd('S', 'S', m, n, A_copy, m, S, U, m, VT, k, work, lwork, info)
        lwork = int(work(1))
        deallocate(work)
        allocate(work(lwork))
        
        ! Compute SVD
        call dgesvd('S', 'S', m, n, A_copy, m, S, U, m, VT, k, work, lwork, info)
        
        deallocate(A_copy, work)
        
    end subroutine compute_svd_internal

    !---------------------------------------------------------------------------
    ! Truncated SVD (for large matrices)
    ! Uses randomized algorithm for efficiency
    !---------------------------------------------------------------------------
    function truncated_svd(A, U, S, VT, m, n, k, n_iter) &
        result(status) bind(C, name="truncated_svd")
        
        integer(c_int), intent(in), value :: m, n, k, n_iter
        real(c_double), intent(in) :: A(m, n)
        real(c_double), intent(out) :: U(m, k)
        real(c_double), intent(out) :: S(k)
        real(c_double), intent(out) :: VT(k, n)
        integer(c_int) :: status
        
        ! Local variables
        real(dp), allocatable :: Q(:,:), B(:,:), Ub(:,:), Sb(:), VTb(:,:)
        real(dp), allocatable :: omega(:,:), Y(:,:)
        integer :: i, info, l
        
        ! Oversampling
        l = min(k + 10, min(m, n))
        
        allocate(omega(n, l), Y(m, l), Q(m, l))
        allocate(B(l, n), Ub(l, l), Sb(l), VTb(l, n))
        
        ! Random projection
        call random_number(omega)
        
        ! Power iteration for better approximation
        Y = matmul(A, omega)
        do i = 1, n_iter
            Y = matmul(A, matmul(transpose(A), Y))
        end do
        
        ! QR factorization of Y
        call qr_factorization(Y, Q, m, l, info)
        if (info /= 0) then
            status = -1
            deallocate(omega, Y, Q, B, Ub, Sb, VTb)
            return
        end if
        
        ! Project A onto Q
        B = matmul(transpose(Q), A)
        
        ! SVD of small matrix B
        call compute_svd_internal(B, Ub, Sb, VTb, l, n, info)
        if (info /= 0) then
            status = -2
            deallocate(omega, Y, Q, B, Ub, Sb, VTb)
            return
        end if
        
        ! Recover U, S, VT
        U = matmul(Q, Ub(:, 1:k))
        S = Sb(1:k)
        VT = VTb(1:k, :)
        
        status = 0
        deallocate(omega, Y, Q, B, Ub, Sb, VTb)
        
    end function truncated_svd

    !---------------------------------------------------------------------------
    ! QR factorization using LAPACK DGEQRF
    !---------------------------------------------------------------------------
    subroutine qr_factorization(A, Q, m, n, info)
        integer, intent(in) :: m, n
        real(dp), intent(inout) :: A(m, n)
        real(dp), intent(out) :: Q(m, n)
        integer, intent(out) :: info
        
        real(dp), allocatable :: tau(:), work(:)
        integer :: lwork
        
        allocate(tau(min(m, n)))
        
        ! Query workspace
        lwork = -1
        allocate(work(1))
        call dgeqrf(m, n, A, m, tau, work, lwork, info)
        lwork = int(work(1))
        deallocate(work)
        allocate(work(lwork))
        
        ! QR factorization
        call dgeqrf(m, n, A, m, tau, work, lwork, info)
        if (info /= 0) then
            deallocate(tau, work)
            return
        end if
        
        ! Extract Q
        Q = A
        call dorgqr(m, n, n, Q, m, tau, work, lwork, info)
        
        deallocate(tau, work)
        
    end subroutine qr_factorization

end module pca_svd
