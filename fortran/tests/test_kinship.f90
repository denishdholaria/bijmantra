!===============================================================================
! Test Suite for Kinship Matrix Computation
! Bijmantra Plant Breeding Platform
!===============================================================================

program test_kinship
    use iso_fortran_env, only: real64
    use kinship
    implicit none
    
    integer, parameter :: dp = real64
    logical :: all_passed
    
    all_passed = .true.
    
    print *, "Running Kinship Matrix Tests..."
    print *, "================================"
    
    call test_grm_vanraden1(all_passed)
    call test_grm_vanraden2(all_passed)
    call test_dominance(all_passed)
    
    print *, ""
    if (all_passed) then
        print *, "All tests PASSED!"
        stop 0
    else
        print *, "Some tests FAILED!"
        stop 1
    end if
    
contains

    subroutine test_grm_vanraden1(passed)
        logical, intent(inout) :: passed
        
        integer, parameter :: n = 5, m = 20
        real(dp) :: genotypes(n, m), G(n, n)
        integer :: status, i, j
        
        print *, "Test 1: GRM VanRaden Method 1..."
        
        ! Initialize genotype matrix
        do j = 1, m
            do i = 1, n
                genotypes(i, j) = real(mod(i * j, 3), dp)
            end do
        end do
        
        status = compute_grm_vanraden1(genotypes, G, n, m)
        
        if (status == 0) then
            ! Check diagonal elements are positive
            if (all([(G(i, i) > 0.0_dp, i = 1, n)])) then
                print *, "  Status: PASSED"
                print *, "  Diagonal range:", minval([(G(i, i), i = 1, n)]), &
                         "to", maxval([(G(i, i), i = 1, n)])
            else
                print *, "  Status: FAILED (negative diagonal)"
                passed = .false.
            end if
        else
            print *, "  Status: FAILED (error code:", status, ")"
            passed = .false.
        end if
        
    end subroutine test_grm_vanraden1

    subroutine test_grm_vanraden2(passed)
        logical, intent(inout) :: passed
        
        integer, parameter :: n = 5, m = 20
        real(dp) :: genotypes(n, m), G(n, n)
        integer :: status, i, j
        
        print *, "Test 2: GRM VanRaden Method 2..."
        
        ! Initialize genotype matrix
        do j = 1, m
            do i = 1, n
                genotypes(i, j) = real(mod(i + j, 3), dp)
            end do
        end do
        
        status = compute_grm_vanraden2(genotypes, G, n, m)
        
        if (status == 0) then
            print *, "  Status: PASSED"
            print *, "  G(1,1) =", G(1, 1)
            print *, "  G(1,2) =", G(1, 2)
        else
            print *, "  Status: FAILED (error code:", status, ")"
            passed = .false.
        end if
        
    end subroutine test_grm_vanraden2

    subroutine test_dominance(passed)
        logical, intent(inout) :: passed
        
        integer, parameter :: n = 5, m = 20
        real(dp) :: genotypes(n, m), D(n, n)
        integer :: status, i, j
        
        print *, "Test 3: Dominance Relationship Matrix..."
        
        ! Initialize genotype matrix
        do j = 1, m
            do i = 1, n
                genotypes(i, j) = real(mod(i * 2 + j, 3), dp)
            end do
        end do
        
        status = compute_dominance_matrix(genotypes, D, n, m)
        
        if (status == 0) then
            print *, "  Status: PASSED"
            print *, "  D(1,1) =", D(1, 1)
        else
            print *, "  Status: FAILED (error code:", status, ")"
            passed = .false.
        end if
        
    end subroutine test_dominance

end program test_kinship
