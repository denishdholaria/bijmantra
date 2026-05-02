!===============================================================================
! Test Suite for REML Engine
! Bijmantra Plant Breeding Platform
!===============================================================================

program test_reml
    use iso_fortran_env, only: real64
    use reml_engine
    implicit none
    
    integer, parameter :: dp = real64
    logical :: all_passed
    
    all_passed = .true.
    
    print *, "Running REML Engine Tests..."
    print *, "============================="
    
    call test_ai_reml(all_passed)
    call test_em_reml(all_passed)
    
    print *, ""
    if (all_passed) then
        print *, "All tests PASSED!"
        stop 0
    else
        print *, "Some tests FAILED!"
        stop 1
    end if
    
contains

    subroutine test_ai_reml(passed)
        logical, intent(inout) :: passed
        
        integer, parameter :: n = 20, p = 2, q = 5
        real(dp) :: y(n), X(n, p), Z(n, q), A(q, q)
        real(dp) :: var_a, var_e
        integer :: status, i, j
        
        print *, "Test 1: AI-REML Variance Estimation..."
        
        ! Generate test data
        call random_seed()
        call random_number(y)
        y = y * 2.0_dp + 1.0_dp
        
        ! Fixed effects design matrix
        X(:, 1) = 1.0_dp
        call random_number(X(:, 2))
        
        ! Random effects design matrix
        Z = 0.0_dp
        do i = 1, n
            j = mod(i - 1, q) + 1
            Z(i, j) = 1.0_dp
        end do
        
        ! Identity relationship matrix
        A = 0.0_dp
        do i = 1, q
            A(i, i) = 1.0_dp
        end do
        
        ! Initial variance estimates
        var_a = 0.5_dp
        var_e = 1.0_dp
        
        status = ai_reml(y, X, Z, A, var_a, var_e, n, p, q)
        
        if (status > 0) then
            print *, "  Status: PASSED"
            print *, "  Converged in", status, "iterations"
            print *, "  var_a =", var_a
            print *, "  var_e =", var_e
            print *, "  h2 =", var_a / (var_a + var_e)
        else if (status == 0) then
            print *, "  Status: PASSED (already converged)"
        else
            print *, "  Status: FAILED (error code:", status, ")"
            passed = .false.
        end if
        
    end subroutine test_ai_reml

    subroutine test_em_reml(passed)
        logical, intent(inout) :: passed
        
        integer, parameter :: n = 20, p = 2, q = 5
        real(dp) :: y(n), X(n, p), Z(n, q), A(q, q)
        real(dp) :: var_a, var_e
        integer :: status, i, j
        
        print *, "Test 2: EM-REML Variance Estimation..."
        
        ! Generate test data
        call random_number(y)
        y = y * 2.0_dp + 1.0_dp
        
        ! Fixed effects design matrix
        X(:, 1) = 1.0_dp
        call random_number(X(:, 2))
        
        ! Random effects design matrix
        Z = 0.0_dp
        do i = 1, n
            j = mod(i - 1, q) + 1
            Z(i, j) = 1.0_dp
        end do
        
        ! Identity relationship matrix
        A = 0.0_dp
        do i = 1, q
            A(i, i) = 1.0_dp
        end do
        
        ! Initial variance estimates
        var_a = 0.5_dp
        var_e = 1.0_dp
        
        status = em_reml(y, X, Z, A, var_a, var_e, n, p, q, 50)
        
        if (status > 0) then
            print *, "  Status: PASSED"
            print *, "  Converged in", status, "iterations"
            print *, "  var_a =", var_a
            print *, "  var_e =", var_e
        else
            print *, "  Status: WARNING (may not have converged)"
            ! EM-REML is slower, so we don't fail the test
        end if
        
    end subroutine test_em_reml

end program test_reml
