!===============================================================================
! G×E Interaction Analysis Module
! Genotype-by-Environment interaction analysis
!
! Bijmantra Plant Breeding Platform
! Aerospace-Grade Numerical Precision
!
! Methods:
! - AMMI (Additive Main effects and Multiplicative Interaction)
! - GGE Biplot
! - Finlay-Wilkinson Regression
!
! Author: Bijmantra Team
! License: MIT
!===============================================================================

module gxe_analysis
    use iso_c_binding
    use iso_fortran_env, only: real64, int32
    use pca_svd, only: compute_svd
    implicit none
    
    private
    public :: ammi_analysis, gge_biplot, finlay_wilkinson
    
    integer, parameter :: dp = real64
    
contains

    !---------------------------------------------------------------------------
    ! AMMI Analysis (Additive Main effects and Multiplicative Interaction)
    !
    ! Model: Y_ij = μ + G_i + E_j + Σ λ_k α_ik γ_jk + ε_ij
    !
    ! Parameters:
    !   Y          - Yield matrix (g x e), genotypes in rows, environments in cols
    !   g_effects  - Output: Genotype main effects (g)
    !   e_effects  - Output: Environment main effects (e)
    !   g_scores   - Output: Genotype IPCA scores (g x k)
    !   e_scores   - Output: Environment IPCA scores (e x k)
    !   eigenvalues- Output: Eigenvalues (k)
    !   grand_mean - Output: Grand mean
    !   g, e       - Number of genotypes and environments
    !   k          - Number of IPCA axes to retain
    !
    ! Returns: 0 on success
    !---------------------------------------------------------------------------
    function ammi_analysis(Y, g_effects, e_effects, g_scores, e_scores, &
                          eigenvalues, grand_mean, g, e, k) &
        result(status) bind(C, name="ammi_analysis")
        
        integer(c_int), intent(in), value :: g, e, k
        real(c_double), intent(in) :: Y(g, e)
        real(c_double), intent(out) :: g_effects(g)
        real(c_double), intent(out) :: e_effects(e)
        real(c_double), intent(out) :: g_scores(g, k)
        real(c_double), intent(out) :: e_scores(e, k)
        real(c_double), intent(out) :: eigenvalues(k)
        real(c_double), intent(out) :: grand_mean
        integer(c_int) :: status
        
        ! Local variables
        real(dp), allocatable :: GE(:,:), U(:,:), S(:), VT(:,:)
        real(dp) :: row_mean, col_mean
        integer :: i, j, min_ge, info
        
        min_ge = min(g, e)
        allocate(GE(g, e), U(g, min_ge), S(min_ge), VT(min_ge, e))
        
        ! Compute grand mean
        grand_mean = sum(Y) / real(g * e, dp)
        
        ! Compute genotype effects (row means - grand mean)
        do i = 1, g
            row_mean = sum(Y(i, :)) / real(e, dp)
            g_effects(i) = row_mean - grand_mean
        end do
        
        ! Compute environment effects (column means - grand mean)
        do j = 1, e
            col_mean = sum(Y(:, j)) / real(g, dp)
            e_effects(j) = col_mean - grand_mean
        end do
        
        ! Compute GE interaction matrix
        do j = 1, e
            do i = 1, g
                GE(i, j) = Y(i, j) - grand_mean - g_effects(i) - e_effects(j)
            end do
        end do
        
        ! SVD of GE interaction matrix
        status = compute_svd(GE, U, S, VT, g, e)
        if (status /= 0) then
            deallocate(GE, U, S, VT)
            return
        end if
        
        ! Extract IPCA scores
        do i = 1, k
            g_scores(:, i) = U(:, i) * sqrt(S(i))
            e_scores(:, i) = VT(i, :) * sqrt(S(i))
            eigenvalues(i) = S(i)**2
        end do
        
        status = 0
        deallocate(GE, U, S, VT)
        
    end function ammi_analysis

    !---------------------------------------------------------------------------
    ! GGE Biplot Analysis
    !
    ! Model: Y_ij - μ - E_j = Σ λ_k α_ik γ_jk
    ! (Environment-centered, genotype + GE combined)
    !
    ! Parameters:
    !   Y          - Yield matrix (g x e)
    !   g_scores   - Output: Genotype scores (g x k)
    !   e_scores   - Output: Environment scores (e x k)
    !   eigenvalues- Output: Eigenvalues (k)
    !   g, e       - Dimensions
    !   k          - Number of PCs
    !   scaling    - Scaling method (0=symmetric, 1=genotype, 2=environment)
    !
    ! Returns: 0 on success
    !---------------------------------------------------------------------------
    function gge_biplot(Y, g_scores, e_scores, eigenvalues, g, e, k, scaling) &
        result(status) bind(C, name="gge_biplot")
        
        integer(c_int), intent(in), value :: g, e, k, scaling
        real(c_double), intent(in) :: Y(g, e)
        real(c_double), intent(out) :: g_scores(g, k)
        real(c_double), intent(out) :: e_scores(e, k)
        real(c_double), intent(out) :: eigenvalues(k)
        integer(c_int) :: status
        
        ! Local variables
        real(dp), allocatable :: Y_centered(:,:), U(:,:), S(:), VT(:,:)
        real(dp) :: col_mean
        integer :: i, j, min_ge
        real(dp) :: scale_g, scale_e
        
        min_ge = min(g, e)
        allocate(Y_centered(g, e), U(g, min_ge), S(min_ge), VT(min_ge, e))
        
        ! Environment-center the data
        do j = 1, e
            col_mean = sum(Y(:, j)) / real(g, dp)
            Y_centered(:, j) = Y(:, j) - col_mean
        end do
        
        ! SVD
        status = compute_svd(Y_centered, U, S, VT, g, e)
        if (status /= 0) then
            deallocate(Y_centered, U, S, VT)
            return
        end if
        
        ! Apply scaling
        do i = 1, k
            select case (scaling)
            case (0)  ! Symmetric
                scale_g = sqrt(S(i))
                scale_e = sqrt(S(i))
            case (1)  ! Genotype-focused
                scale_g = S(i)
                scale_e = 1.0_dp
            case (2)  ! Environment-focused
                scale_g = 1.0_dp
                scale_e = S(i)
            case default
                scale_g = sqrt(S(i))
                scale_e = sqrt(S(i))
            end select
            
            g_scores(:, i) = U(:, i) * scale_g
            e_scores(:, i) = VT(i, :) * scale_e
            eigenvalues(i) = S(i)**2
        end do
        
        status = 0
        deallocate(Y_centered, U, S, VT)
        
    end function gge_biplot

    !---------------------------------------------------------------------------
    ! Finlay-Wilkinson Regression
    !
    ! Model: Y_ij = μ_i + β_i * E_j + ε_ij
    ! where E_j is the environment mean
    !
    ! Parameters:
    !   Y          - Yield matrix (g x e)
    !   means      - Output: Genotype means (g)
    !   slopes     - Output: Regression slopes (g)
    !   r_squared  - Output: R² values (g)
    !   env_index  - Output: Environment index (e)
    !   g, e       - Dimensions
    !
    ! Returns: 0 on success
    !---------------------------------------------------------------------------
    function finlay_wilkinson(Y, means, slopes, r_squared, env_index, g, e) &
        result(status) bind(C, name="finlay_wilkinson")
        
        integer(c_int), intent(in), value :: g, e
        real(c_double), intent(in) :: Y(g, e)
        real(c_double), intent(out) :: means(g)
        real(c_double), intent(out) :: slopes(g)
        real(c_double), intent(out) :: r_squared(g)
        real(c_double), intent(out) :: env_index(e)
        integer(c_int) :: status
        
        ! Local variables
        real(dp) :: grand_mean, env_mean
        real(dp) :: sum_x, sum_y, sum_xy, sum_xx, sum_yy
        real(dp) :: mean_x, mean_y, ss_x, ss_y, ss_xy
        integer :: i, j
        
        ! Compute grand mean
        grand_mean = sum(Y) / real(g * e, dp)
        
        ! Compute environment index (environment mean - grand mean)
        do j = 1, e
            env_mean = sum(Y(:, j)) / real(g, dp)
            env_index(j) = env_mean - grand_mean
        end do
        
        ! Regression for each genotype
        do i = 1, g
            ! Compute genotype mean
            means(i) = sum(Y(i, :)) / real(e, dp)
            
            ! Simple linear regression: Y_ij = a + b * env_index_j
            sum_x = sum(env_index)
            sum_y = sum(Y(i, :))
            sum_xy = 0.0_dp
            sum_xx = 0.0_dp
            sum_yy = 0.0_dp
            
            do j = 1, e
                sum_xy = sum_xy + env_index(j) * Y(i, j)
                sum_xx = sum_xx + env_index(j) * env_index(j)
                sum_yy = sum_yy + Y(i, j) * Y(i, j)
            end do
            
            mean_x = sum_x / real(e, dp)
            mean_y = sum_y / real(e, dp)
            
            ss_x = sum_xx - real(e, dp) * mean_x * mean_x
            ss_y = sum_yy - real(e, dp) * mean_y * mean_y
            ss_xy = sum_xy - real(e, dp) * mean_x * mean_y
            
            ! Slope
            if (abs(ss_x) > 1.0d-10) then
                slopes(i) = ss_xy / ss_x
            else
                slopes(i) = 1.0_dp
            end if
            
            ! R²
            if (abs(ss_y) > 1.0d-10 .and. abs(ss_x) > 1.0d-10) then
                r_squared(i) = (ss_xy * ss_xy) / (ss_x * ss_y)
            else
                r_squared(i) = 0.0_dp
            end if
        end do
        
        status = 0
        
    end function finlay_wilkinson

end module gxe_analysis
