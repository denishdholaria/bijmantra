!===============================================================================
! Test Suite for BLUP Solver
! Bijmantra Plant Breeding Platform
!===============================================================================

program test_blup
    use iso_fortran_env, only: real64
    use blup_solver
    implicit none
    
    integer, parameter :: dp = real64
    logical :: all_passed
    
    all_passed = .true.
    
    print *, "Running BLUP Solver Tests..."
    print *, "=============================="
    
    call test_simple_blup(all_passed)
    call test_gblup_small(all_passed)
    call test_mme_solver(all_passed)
    
    print *, ""
    if (all_passed) then
        print *, "All tests PASSED!"
        stop 0
    else
        print *, "Some tests FAILED!"
        stop 1
    end if
    
contains

    subroutine test_simple_blup(passed)
        logical, intent(inout) :: passed
        
        integer, parameter :: n = 10, p = 2, q = 5
        real(dp) :: y(n), X(n, p), Z(n, q), A_inv(q, q)
        real(dp) :: beta(p), u(q)
        real(dp) :: var_a, var_e
        integer :: status, i, j
        
        print *, "Test 1: Simple BLUP..."
        
        ! Initialize test data
        y = [1.2_dp, 2.3_dp, 1.8_dp, 2.1_dp, 1.9_dp, &
             2.5_dp, 1.7_dp, 2.2_dp, 1.6_dp, 2.0_dp]
        
        ! Fixed effects design matrix (intercept + one covariate)
        X(:, 1) = 1.0_dp
        X(:, 2) = [0.5_dp, 1.0_dp, 0.3_dp, 0.8_dp, 0.6_dp, &
                   1.2_dp, 0.4_dp, 0.9_dp, 0.2_dp, 0.7_dp]
        
        ! Random effects design matrix
        Z = 0.0_dp
        do i = 1, n
            j = mod(i - 1, q) + 1
            Z(i, j) = 1.0_dp
        end do
        
        ! Identity relationship matrix inverse
        A_inv = 0.0_dp
        do i = 1, q
            A_inv(i, i) = 1.0_dp
        end do
        
        var_a = 0.5_dp
        var_e = 1.0_dp
        
        status = compute_blup(y, X, Z, A_inv, var_a, var_e, beta, u, n, p, q)
        
        if (status == 0) then
            print *, "  Status: PASSED"
            print *, "  Beta(1) =", beta(1)
            print *, "  Beta(2) =", beta(2)
        else
            print *, "  Status: FAILED (error code:", status, ")"
            passed = .false.
        end if
        
    end subroutine test_simple_blup

    subroutine test_gblup_small(passed)
        logical, intent(inout) :: passed
        
        integer, parameter :: n = 5, m = 10
        real(dp) :: genotypes(n, m), phenotypes(n), gebv(n)
        real(dp) :: h2
        integer :: status, i, j
        
        print *, "Test 2: Small GBLUP..."
        
        ! Initialize genotype matrix (0, 1, 2 coding)
        do j = 1, m
            do i = 1, n
                genotypes(i, j) = real(mod(i + j, 3), dp)
            end do
        end do
        
        ! Phenotypes
        phenotypes = [2.5_dp, 3.1_dp, 2.8_dp, 3.5_dp, 2.9_dp]
        
        h2 = 0.4_dp
        
        status = compute_gblup(genotypes, phenotypes, gebv, n, m, h2)
        
        if (status == 0) then
            print *, "  Status: PASSED"
            print *, "  GEBV range:", minval(gebv), "to", maxval(gebv)
        else
            print *, "  Status: FAILED (error code:", status, ")"
            passed = .false.
        end if
        
    end subroutine test_gblup_small

    subroutine test_mme_solver(passed)
        logical, intent(inout) :: passed
        
        integer, parameter :: dim = 5
        real(dp) :: C(dim, dim), rhs(dim), solution(dim)
        real(dp) :: tol
        integer :: max_iter, iterations, i
        
        print *, "Test 3: MME PCG Solver..."
        
        ! Create a simple positive definite matrix
        C = 0.0_dp
        do i = 1, dim
            C(i, i) = 4.0_dp
            if (i > 1) C(i, i-1) = -1.0_dp
            if (i < dim) C(i, i+1) = -1.0_dp
        end do
        
        rhs = [1.0_dp, 2.0_dp, 3.0_dp, 2.0_dp, 1.0_dp]
        solution = 0.0_dp
        tol = 1.0d-8
        max_iter = 100
        
        iterations = solve_mme(C, rhs, solution, dim, tol, max_iter)
        
        if (iterations > 0) then
            print *, "  Status: PASSED"
            print *, "  Converged in", iterations, "iterations"
        else
            print *, "  Status: FAILED (iterations:", iterations, ")"
            passed = .false.
        end if
        
    end subroutine test_mme_solver

end program test_blup
