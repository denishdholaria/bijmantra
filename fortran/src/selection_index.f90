!===============================================================================
! Selection Index Module
! Multi-trait selection index computation
!
! Bijmantra Plant Breeding Platform
! Aerospace-Grade Numerical Precision
!
! Methods:
! - Smith-Hazel Index
! - Desired Gains Index
! - Restricted Selection Index
!
! Author: Bijmantra Team
! License: MIT
!===============================================================================

module selection_index
    use iso_c_binding
    use iso_fortran_env, only: real64
    implicit none
    
    private
    public :: smith_hazel_index, desired_gains_index, compute_selection_response
    
    integer, parameter :: dp = real64
    
contains

    !---------------------------------------------------------------------------
    ! Smith-Hazel Selection Index
    !
    ! I = b'P where b = P⁻¹Ga
    ! P = phenotypic variance-covariance matrix
    ! G = genetic variance-covariance matrix
    ! a = economic weights
    !
    ! Parameters:
    !   P          - Phenotypic covariance matrix (t x t)
    !   G          - Genetic covariance matrix (t x t)
    !   a          - Economic weights (t)
    !   b          - Output: Index coefficients (t)
    !   t          - Number of traits
    !
    ! Returns: 0 on success
    !---------------------------------------------------------------------------
    function smith_hazel_index(P, G, a, b, t) &
        result(status) bind(C, name="smith_hazel_index")
        
        integer(c_int), intent(in), value :: t
        real(c_double), intent(in) :: P(t, t)
        real(c_double), intent(in) :: G(t, t)
        real(c_double), intent(in) :: a(t)
        real(c_double), intent(out) :: b(t)
        integer(c_int) :: status
        
        real(dp), allocatable :: P_inv(:,:), Ga(:)
        integer :: info
        
        allocate(P_inv(t, t), Ga(t))
        
        ! Compute Ga
        Ga = matmul(G, a)
        
        ! Invert P
        P_inv = P
        call matrix_inverse(P_inv, t, info)
        
        if (info /= 0) then
            status = -1
            deallocate(P_inv, Ga)
            return
        end if
        
        ! b = P⁻¹Ga
        b = matmul(P_inv, Ga)
        
        status = 0
        deallocate(P_inv, Ga)
        
    end function smith_hazel_index

    !---------------------------------------------------------------------------
    ! Desired Gains Selection Index
    !
    ! Pesek-Baker method: b = P⁻¹Gd
    ! where d = desired genetic gains
    !---------------------------------------------------------------------------
    function desired_gains_index(P, G, d, b, t) &
        result(status) bind(C, name="desired_gains_index")
        
        integer(c_int), intent(in), value :: t
        real(c_double), intent(in) :: P(t, t)
        real(c_double), intent(in) :: G(t, t)
        real(c_double), intent(in) :: d(t)  ! Desired gains
        real(c_double), intent(out) :: b(t)
        integer(c_int) :: status
        
        real(dp), allocatable :: P_inv(:,:), Gd(:)
        integer :: info
        
        allocate(P_inv(t, t), Gd(t))
        
        ! Compute Gd
        Gd = matmul(G, d)
        
        ! Invert P
        P_inv = P
        call matrix_inverse(P_inv, t, info)
        
        if (info /= 0) then
            status = -1
            deallocate(P_inv, Gd)
            return
        end if
        
        ! b = P⁻¹Gd
        b = matmul(P_inv, Gd)
        
        status = 0
        deallocate(P_inv, Gd)
        
    end function desired_gains_index

    !---------------------------------------------------------------------------
    ! Compute Selection Response
    !
    ! R = i * σ_I * r_AI
    ! where:
    !   i = selection intensity
    !   σ_I = standard deviation of index
    !   r_AI = correlation between index and aggregate genotype
    !
    ! Parameters:
    !   b          - Index coefficients (t)
    !   P          - Phenotypic covariance matrix (t x t)
    !   G          - Genetic covariance matrix (t x t)
    !   a          - Economic weights (t)
    !   intensity  - Selection intensity
    !   response   - Output: Expected response per trait (t)
    !   accuracy   - Output: Selection accuracy (r_AI)
    !   t          - Number of traits
    !
    ! Returns: 0 on success
    !---------------------------------------------------------------------------
    function compute_selection_response(b, P, G, a, intensity, response, accuracy, t) &
        result(status) bind(C, name="compute_selection_response")
        
        integer(c_int), intent(in), value :: t
        real(c_double), intent(in) :: b(t)
        real(c_double), intent(in) :: P(t, t)
        real(c_double), intent(in) :: G(t, t)
        real(c_double), intent(in) :: a(t)
        real(c_double), intent(in), value :: intensity
        real(c_double), intent(out) :: response(t)
        real(c_double), intent(out) :: accuracy
        integer(c_int) :: status
        
        real(dp) :: var_I, var_A, cov_IA
        real(dp) :: sigma_I, sigma_A
        integer :: i
        
        ! Variance of index: σ²_I = b'Pb
        var_I = dot_product(b, matmul(P, b))
        sigma_I = sqrt(max(var_I, 0.0_dp))
        
        ! Variance of aggregate genotype: σ²_A = a'Ga
        var_A = dot_product(a, matmul(G, a))
        sigma_A = sqrt(max(var_A, 0.0_dp))
        
        ! Covariance: Cov(I, A) = b'Ga
        cov_IA = dot_product(b, matmul(G, a))
        
        ! Accuracy: r_AI = Cov(I,A) / (σ_I * σ_A)
        if (sigma_I > 1.0d-10 .and. sigma_A > 1.0d-10) then
            accuracy = cov_IA / (sigma_I * sigma_A)
        else
            accuracy = 0.0_dp
        end if
        
        ! Response per trait: R_j = i * (b'G_j) / σ_I
        if (sigma_I > 1.0d-10) then
            do i = 1, t
                response(i) = intensity * dot_product(b, G(:, i)) / sigma_I
            end do
        else
            response = 0.0_dp
        end if
        
        status = 0
        
    end function compute_selection_response

    !---------------------------------------------------------------------------
    ! Matrix inverse using LAPACK
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

end module selection_index
