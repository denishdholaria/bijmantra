!===============================================================================
! Linkage Disequilibrium Analysis Module
! LD computation and decay analysis
!
! Bijmantra Plant Breeding Platform
! Aerospace-Grade Numerical Precision
!
! Author: Bijmantra Team
! License: MIT
!===============================================================================

module ld_analysis
    use iso_c_binding
    use iso_fortran_env, only: real64, int32
    implicit none
    
    private
    public :: compute_r2, compute_dprime, compute_ld_matrix, ld_decay
    
    integer, parameter :: dp = real64
    
contains

    !---------------------------------------------------------------------------
    ! Compute r² (squared correlation) between two markers
    !
    ! Parameters:
    !   geno1, geno2 - Genotype vectors (n x 1), coded as 0, 1, 2
    !   n            - Number of individuals
    !
    ! Returns: r² value
    !---------------------------------------------------------------------------
    function compute_r2(geno1, geno2, n) result(r2) bind(C, name="compute_r2")
        integer(c_int), intent(in), value :: n
        real(c_double), intent(in) :: geno1(n), geno2(n)
        real(c_double) :: r2
        
        real(dp) :: mean1, mean2, var1, var2, cov
        real(dp) :: sum1, sum2, sum11, sum22, sum12
        integer :: i, valid_n
        
        sum1 = 0.0_dp
        sum2 = 0.0_dp
        sum11 = 0.0_dp
        sum22 = 0.0_dp
        sum12 = 0.0_dp
        valid_n = 0
        
        do i = 1, n
            ! Skip missing values (coded as negative)
            if (geno1(i) >= 0.0_dp .and. geno2(i) >= 0.0_dp) then
                valid_n = valid_n + 1
                sum1 = sum1 + geno1(i)
                sum2 = sum2 + geno2(i)
                sum11 = sum11 + geno1(i) * geno1(i)
                sum22 = sum22 + geno2(i) * geno2(i)
                sum12 = sum12 + geno1(i) * geno2(i)
            end if
        end do
        
        if (valid_n < 2) then
            r2 = 0.0_dp
            return
        end if
        
        mean1 = sum1 / real(valid_n, dp)
        mean2 = sum2 / real(valid_n, dp)
        
        var1 = sum11 / real(valid_n, dp) - mean1 * mean1
        var2 = sum22 / real(valid_n, dp) - mean2 * mean2
        cov = sum12 / real(valid_n, dp) - mean1 * mean2
        
        if (var1 < 1.0d-10 .or. var2 < 1.0d-10) then
            r2 = 0.0_dp
        else
            r2 = (cov * cov) / (var1 * var2)
        end if
        
    end function compute_r2

    !---------------------------------------------------------------------------
    ! Compute D' (normalized LD coefficient)
    !
    ! Parameters:
    !   geno1, geno2 - Genotype vectors (n x 1), coded as 0, 1, 2
    !   n            - Number of individuals
    !
    ! Returns: D' value
    !---------------------------------------------------------------------------
    function compute_dprime(geno1, geno2, n) result(dprime) bind(C, name="compute_dprime")
        integer(c_int), intent(in), value :: n
        real(c_double), intent(in) :: geno1(n), geno2(n)
        real(c_double) :: dprime
        
        real(dp) :: p1, p2, q1, q2
        real(dp) :: p11, D, Dmax
        integer :: i, valid_n
        integer :: n00, n01, n02, n10, n11, n12, n20, n21, n22
        
        ! Count haplotype frequencies (assuming HWE)
        n00 = 0; n01 = 0; n02 = 0
        n10 = 0; n11 = 0; n12 = 0
        n20 = 0; n21 = 0; n22 = 0
        valid_n = 0
        
        do i = 1, n
            if (geno1(i) >= 0.0_dp .and. geno2(i) >= 0.0_dp) then
                valid_n = valid_n + 1
                
                if (nint(geno1(i)) == 0) then
                    if (nint(geno2(i)) == 0) n00 = n00 + 1
                    if (nint(geno2(i)) == 1) n01 = n01 + 1
                    if (nint(geno2(i)) == 2) n02 = n02 + 1
                else if (nint(geno1(i)) == 1) then
                    if (nint(geno2(i)) == 0) n10 = n10 + 1
                    if (nint(geno2(i)) == 1) n11 = n11 + 1
                    if (nint(geno2(i)) == 2) n12 = n12 + 1
                else
                    if (nint(geno2(i)) == 0) n20 = n20 + 1
                    if (nint(geno2(i)) == 1) n21 = n21 + 1
                    if (nint(geno2(i)) == 2) n22 = n22 + 1
                end if
            end if
        end do
        
        if (valid_n < 2) then
            dprime = 0.0_dp
            return
        end if
        
        ! Allele frequencies
        p1 = real(2*n00 + 2*n01 + 2*n02 + n10 + n11 + n12, dp) / real(2 * valid_n, dp)
        p2 = real(2*n00 + 2*n10 + 2*n20 + n01 + n11 + n21, dp) / real(2 * valid_n, dp)
        q1 = 1.0_dp - p1
        q2 = 1.0_dp - p2
        
        ! Haplotype frequency estimate (EM would be better)
        p11 = real(2*n00 + n01 + n10, dp) / real(2 * valid_n, dp)
        
        ! D coefficient
        D = p11 - p1 * p2
        
        ! Normalize
        if (D > 0.0_dp) then
            Dmax = min(p1 * q2, q1 * p2)
        else
            Dmax = min(p1 * p2, q1 * q2)
        end if
        
        if (abs(Dmax) < 1.0d-10) then
            dprime = 0.0_dp
        else
            dprime = abs(D) / Dmax
        end if
        
    end function compute_dprime

    !---------------------------------------------------------------------------
    ! Compute LD matrix (r² for all marker pairs)
    !
    ! Parameters:
    !   genotypes  - Marker matrix (n x m), coded as 0, 1, 2
    !   ld_matrix  - Output: LD matrix (m x m)
    !   n, m       - Dimensions
    !
    ! Returns: 0 on success
    !---------------------------------------------------------------------------
    function compute_ld_matrix(genotypes, ld_matrix, n, m) &
        result(status) bind(C, name="compute_ld_matrix")
        
        integer(c_int), intent(in), value :: n, m
        real(c_double), intent(in) :: genotypes(n, m)
        real(c_double), intent(out) :: ld_matrix(m, m)
        integer(c_int) :: status
        
        integer :: i, j
        
        ! Initialize diagonal
        do i = 1, m
            ld_matrix(i, i) = 1.0_dp
        end do
        
        ! Compute pairwise r²
        !$OMP PARALLEL DO PRIVATE(i, j) SCHEDULE(DYNAMIC)
        do j = 2, m
            do i = 1, j - 1
                ld_matrix(i, j) = compute_r2(genotypes(:, i), genotypes(:, j), n)
                ld_matrix(j, i) = ld_matrix(i, j)
            end do
        end do
        !$OMP END PARALLEL DO
        
        status = 0
        
    end function compute_ld_matrix

    !---------------------------------------------------------------------------
    ! Compute LD decay curve
    !
    ! Parameters:
    !   genotypes  - Marker matrix (n x m)
    !   positions  - Physical positions (m)
    !   distances  - Output: Distance bins
    !   mean_r2    - Output: Mean r² per bin
    !   n_bins     - Number of distance bins
    !   max_dist   - Maximum distance to consider
    !   n, m       - Dimensions
    !
    ! Returns: 0 on success
    !---------------------------------------------------------------------------
    function ld_decay(genotypes, positions, distances, mean_r2, n_bins, max_dist, n, m) &
        result(status) bind(C, name="ld_decay")
        
        integer(c_int), intent(in), value :: n, m, n_bins
        real(c_double), intent(in), value :: max_dist
        real(c_double), intent(in) :: genotypes(n, m)
        real(c_double), intent(in) :: positions(m)
        real(c_double), intent(out) :: distances(n_bins)
        real(c_double), intent(out) :: mean_r2(n_bins)
        integer(c_int) :: status
        
        real(dp) :: bin_width, dist, r2_val
        real(dp), allocatable :: sum_r2(:)
        integer, allocatable :: count(:)
        integer :: i, j, bin_idx
        
        allocate(sum_r2(n_bins), count(n_bins))
        sum_r2 = 0.0_dp
        count = 0
        
        bin_width = max_dist / real(n_bins, dp)
        
        ! Set distance bin centers
        do i = 1, n_bins
            distances(i) = (real(i, dp) - 0.5_dp) * bin_width
        end do
        
        ! Compute pairwise LD and bin by distance
        do j = 2, m
            do i = 1, j - 1
                dist = abs(positions(j) - positions(i))
                
                if (dist <= max_dist) then
                    bin_idx = min(int(dist / bin_width) + 1, n_bins)
                    r2_val = compute_r2(genotypes(:, i), genotypes(:, j), n)
                    
                    sum_r2(bin_idx) = sum_r2(bin_idx) + r2_val
                    count(bin_idx) = count(bin_idx) + 1
                end if
            end do
        end do
        
        ! Compute means
        do i = 1, n_bins
            if (count(i) > 0) then
                mean_r2(i) = sum_r2(i) / real(count(i), dp)
            else
                mean_r2(i) = 0.0_dp
            end if
        end do
        
        status = 0
        deallocate(sum_r2, count)
        
    end function ld_decay

end module ld_analysis
