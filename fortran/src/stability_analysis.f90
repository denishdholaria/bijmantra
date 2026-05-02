!===============================================================================
! Stability Analysis Module
! Yield stability analysis methods
!
! Bijmantra Plant Breeding Platform
! Aerospace-Grade Numerical Precision
!
! Author: Bijmantra Team
! License: MIT
!===============================================================================

module stability_analysis
    use iso_c_binding
    use iso_fortran_env, only: real64
    implicit none
    
    private
    public :: eberhart_russell, wricke_ecovalence, shukla_stability
    
    integer, parameter :: dp = real64
    
contains

    !---------------------------------------------------------------------------
    ! Eberhart-Russell Stability Analysis
    ! Computes regression coefficient and deviation from regression
    !---------------------------------------------------------------------------
    function eberhart_russell(Y, means, bi, s2di, g, e) &
        result(status) bind(C, name="eberhart_russell")
        
        integer(c_int), intent(in), value :: g, e
        real(c_double), intent(in) :: Y(g, e)
        real(c_double), intent(out) :: means(g)
        real(c_double), intent(out) :: bi(g)      ! Regression coefficient
        real(c_double), intent(out) :: s2di(g)    ! Deviation variance
        integer(c_int) :: status
        
        real(dp), allocatable :: env_index(:), predicted(:)
        real(dp) :: grand_mean, sum_Ij2, sum_xy, sum_dev2
        integer :: i, j
        
        allocate(env_index(e), predicted(e))
        
        ! Grand mean
        grand_mean = sum(Y) / real(g * e, dp)
        
        ! Environment index
        do j = 1, e
            env_index(j) = sum(Y(:, j)) / real(g, dp) - grand_mean
        end do
        
        sum_Ij2 = sum(env_index**2)
        
        ! For each genotype
        do i = 1, g
            means(i) = sum(Y(i, :)) / real(e, dp)
            
            ! Regression coefficient
            sum_xy = 0.0_dp
            do j = 1, e
                sum_xy = sum_xy + (Y(i, j) - means(i)) * env_index(j)
            end do
            
            if (abs(sum_Ij2) > 1.0d-10) then
                bi(i) = sum_xy / sum_Ij2
            else
                bi(i) = 1.0_dp
            end if
            
            ! Deviation from regression
            sum_dev2 = 0.0_dp
            do j = 1, e
                predicted(j) = means(i) + bi(i) * env_index(j)
                sum_dev2 = sum_dev2 + (Y(i, j) - predicted(j))**2
            end do
            
            s2di(i) = sum_dev2 / real(e - 2, dp)
        end do
        
        status = 0
        deallocate(env_index, predicted)
        
    end function eberhart_russell

    !---------------------------------------------------------------------------
    ! Wricke's Ecovalence
    ! W_i = Σ_j (Y_ij - Y_i. - Y_.j + Y_..)²
    !---------------------------------------------------------------------------
    function wricke_ecovalence(Y, ecovalence, g, e) &
        result(status) bind(C, name="wricke_ecovalence")
        
        integer(c_int), intent(in), value :: g, e
        real(c_double), intent(in) :: Y(g, e)
        real(c_double), intent(out) :: ecovalence(g)
        integer(c_int) :: status
        
        real(dp), allocatable :: g_means(:), e_means(:)
        real(dp) :: grand_mean, interaction
        integer :: i, j
        
        allocate(g_means(g), e_means(e))
        
        grand_mean = sum(Y) / real(g * e, dp)
        
        do i = 1, g
            g_means(i) = sum(Y(i, :)) / real(e, dp)
        end do
        
        do j = 1, e
            e_means(j) = sum(Y(:, j)) / real(g, dp)
        end do
        
        do i = 1, g
            ecovalence(i) = 0.0_dp
            do j = 1, e
                interaction = Y(i, j) - g_means(i) - e_means(j) + grand_mean
                ecovalence(i) = ecovalence(i) + interaction**2
            end do
        end do
        
        status = 0
        deallocate(g_means, e_means)
        
    end function wricke_ecovalence

    !---------------------------------------------------------------------------
    ! Shukla's Stability Variance
    !---------------------------------------------------------------------------
    function shukla_stability(Y, sigma2i, g, e) &
        result(status) bind(C, name="shukla_stability")
        
        integer(c_int), intent(in), value :: g, e
        real(c_double), intent(in) :: Y(g, e)
        real(c_double), intent(out) :: sigma2i(g)
        integer(c_int) :: status
        
        real(dp), allocatable :: g_means(:), e_means(:), W(:)
        real(dp) :: grand_mean, sum_W
        integer :: i
        
        allocate(g_means(g), e_means(e), W(g))
        
        ! First compute ecovalence
        status = wricke_ecovalence(Y, W, g, e)
        if (status /= 0) then
            deallocate(g_means, e_means, W)
            return
        end if
        
        sum_W = sum(W)
        
        ! Shukla's variance
        do i = 1, g
            sigma2i(i) = (real(g, dp) * W(i) - sum_W) / &
                         (real((g - 1) * (g - 2) * (e - 1), dp))
        end do
        
        status = 0
        deallocate(g_means, e_means, W)
        
    end function shukla_stability

end module stability_analysis
