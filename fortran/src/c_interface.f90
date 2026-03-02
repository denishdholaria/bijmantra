!===============================================================================
! C Interface Module
! Exposes Fortran routines to C/Rust via iso_c_binding
!
! Bijmantra Plant Breeding Platform
! Aerospace-Grade Numerical Precision
!
! This module provides the C ABI interface for all Fortran compute kernels,
! enabling safe calls from Rust and other languages.
!
! Author: Bijmantra Team
! License: MIT
!===============================================================================

module c_interface
    use iso_c_binding
    use blup_solver
    use kinship
    use reml_engine
    implicit none
    
contains

    !---------------------------------------------------------------------------
    ! Version and Info
    !---------------------------------------------------------------------------
    subroutine get_version(major, minor, patch) bind(C, name="bijmantra_get_version")
        integer(c_int), intent(out) :: major, minor, patch
        major = 0
        minor = 1
        patch = 0
    end subroutine get_version

    function get_compute_capabilities() result(caps) bind(C, name="bijmantra_get_capabilities")
        integer(c_int) :: caps
        ! Bit flags for capabilities
        ! Bit 0: BLUP
        ! Bit 1: GBLUP
        ! Bit 2: REML
        ! Bit 3: GRM
        ! Bit 4: LD Analysis
        ! Bit 5: G×E Analysis
        ! Bit 6: OpenMP
        ! Bit 7: MKL
        caps = 63  ! All basic capabilities enabled (bits 0-5)
        
#ifdef _OPENMP
        caps = ior(caps, 64)  ! OpenMP enabled
#endif

#ifdef USE_MKL
        caps = ior(caps, 128)  ! MKL enabled
#endif
        
    end function get_compute_capabilities

    !---------------------------------------------------------------------------
    ! Memory Management Helpers
    !---------------------------------------------------------------------------
    function allocate_matrix(rows, cols) result(ptr) bind(C, name="bijmantra_alloc_matrix")
        integer(c_int), intent(in), value :: rows, cols
        type(c_ptr) :: ptr
        real(c_double), pointer :: matrix(:,:)
        
        allocate(matrix(rows, cols))
        matrix = 0.0d0
        ptr = c_loc(matrix(1,1))
    end function allocate_matrix

    subroutine free_matrix(ptr, rows, cols) bind(C, name="bijmantra_free_matrix")
        type(c_ptr), intent(in), value :: ptr
        integer(c_int), intent(in), value :: rows, cols
        real(c_double), pointer :: matrix(:,:)
        
        call c_f_pointer(ptr, matrix, [rows, cols])
        deallocate(matrix)
    end subroutine free_matrix

    !---------------------------------------------------------------------------
    ! Wrapper: Compute BLUP
    !---------------------------------------------------------------------------
    function c_compute_blup(y_ptr, x_ptr, z_ptr, a_inv_ptr, var_a, var_e, &
                            beta_ptr, u_ptr, n, p, q) &
        result(status) bind(C, name="bijmantra_compute_blup")
        
        type(c_ptr), intent(in), value :: y_ptr, x_ptr, z_ptr, a_inv_ptr
        type(c_ptr), intent(in), value :: beta_ptr, u_ptr
        real(c_double), intent(in), value :: var_a, var_e
        integer(c_int), intent(in), value :: n, p, q
        integer(c_int) :: status
        
        real(c_double), pointer :: y(:), X(:,:), Z(:,:), A_inv(:,:)
        real(c_double), pointer :: beta(:), u(:)
        
        ! Convert C pointers to Fortran arrays
        call c_f_pointer(y_ptr, y, [n])
        call c_f_pointer(x_ptr, X, [n, p])
        call c_f_pointer(z_ptr, Z, [n, q])
        call c_f_pointer(a_inv_ptr, A_inv, [q, q])
        call c_f_pointer(beta_ptr, beta, [p])
        call c_f_pointer(u_ptr, u, [q])
        
        ! Call the actual computation
        status = compute_blup(y, X, Z, A_inv, var_a, var_e, beta, u, n, p, q)
        
    end function c_compute_blup

    !---------------------------------------------------------------------------
    ! Wrapper: Compute GBLUP
    !---------------------------------------------------------------------------
    function c_compute_gblup(geno_ptr, pheno_ptr, gebv_ptr, n, m, h2) &
        result(status) bind(C, name="bijmantra_compute_gblup")
        
        type(c_ptr), intent(in), value :: geno_ptr, pheno_ptr, gebv_ptr
        integer(c_int), intent(in), value :: n, m
        real(c_double), intent(in), value :: h2
        integer(c_int) :: status
        
        real(c_double), pointer :: genotypes(:,:), phenotypes(:), gebv(:)
        
        call c_f_pointer(geno_ptr, genotypes, [n, m])
        call c_f_pointer(pheno_ptr, phenotypes, [n])
        call c_f_pointer(gebv_ptr, gebv, [n])
        
        status = compute_gblup(genotypes, phenotypes, gebv, n, m, h2)
        
    end function c_compute_gblup

    !---------------------------------------------------------------------------
    ! Wrapper: Compute GRM (VanRaden Method 1)
    !---------------------------------------------------------------------------
    function c_compute_grm_v1(geno_ptr, g_ptr, n, m) &
        result(status) bind(C, name="bijmantra_compute_grm_v1")
        
        type(c_ptr), intent(in), value :: geno_ptr, g_ptr
        integer(c_int), intent(in), value :: n, m
        integer(c_int) :: status
        
        real(c_double), pointer :: genotypes(:,:), G(:,:)
        
        call c_f_pointer(geno_ptr, genotypes, [n, m])
        call c_f_pointer(g_ptr, G, [n, n])
        
        status = compute_grm_vanraden1(genotypes, G, n, m)
        
    end function c_compute_grm_v1

    !---------------------------------------------------------------------------
    ! Wrapper: Compute GRM (VanRaden Method 2)
    !---------------------------------------------------------------------------
    function c_compute_grm_v2(geno_ptr, g_ptr, n, m) &
        result(status) bind(C, name="bijmantra_compute_grm_v2")
        
        type(c_ptr), intent(in), value :: geno_ptr, g_ptr
        integer(c_int), intent(in), value :: n, m
        integer(c_int) :: status
        
        real(c_double), pointer :: genotypes(:,:), G(:,:)
        
        call c_f_pointer(geno_ptr, genotypes, [n, m])
        call c_f_pointer(g_ptr, G, [n, n])
        
        status = compute_grm_vanraden2(genotypes, G, n, m)
        
    end function c_compute_grm_v2

    !---------------------------------------------------------------------------
    ! Wrapper: Compute Dominance Matrix
    !---------------------------------------------------------------------------
    function c_compute_dominance(geno_ptr, d_ptr, n, m) &
        result(status) bind(C, name="bijmantra_compute_dominance")
        
        type(c_ptr), intent(in), value :: geno_ptr, d_ptr
        integer(c_int), intent(in), value :: n, m
        integer(c_int) :: status
        
        real(c_double), pointer :: genotypes(:,:), D(:,:)
        
        call c_f_pointer(geno_ptr, genotypes, [n, m])
        call c_f_pointer(d_ptr, D, [n, n])
        
        status = compute_dominance_matrix(genotypes, D, n, m)
        
    end function c_compute_dominance

    !---------------------------------------------------------------------------
    ! Wrapper: Estimate Variance Components (AI-REML)
    !---------------------------------------------------------------------------
    function c_estimate_varcomp(y_ptr, x_ptr, z_ptr, a_ptr, var_a, var_e, &
                                n, p, q, tol, max_iter) &
        result(iterations) bind(C, name="bijmantra_estimate_varcomp")
        
        type(c_ptr), intent(in), value :: y_ptr, x_ptr, z_ptr, a_ptr
        real(c_double), intent(inout) :: var_a, var_e
        integer(c_int), intent(in), value :: n, p, q, max_iter
        real(c_double), intent(in), value :: tol
        integer(c_int) :: iterations
        
        real(c_double), pointer :: y(:), X(:,:), Z(:,:), A(:,:)
        
        call c_f_pointer(y_ptr, y, [n])
        call c_f_pointer(x_ptr, X, [n, p])
        call c_f_pointer(z_ptr, Z, [n, q])
        call c_f_pointer(a_ptr, A, [q, q])
        
        iterations = estimate_variance_components(y, X, Z, A, var_a, var_e, &
                                                  n, p, q, tol, max_iter)
        
    end function c_estimate_varcomp

    !---------------------------------------------------------------------------
    ! Wrapper: Solve MME using PCG
    !---------------------------------------------------------------------------
    function c_solve_mme(c_ptr_in, rhs_ptr, sol_ptr, dim, tol, max_iter) &
        result(iterations) bind(C, name="bijmantra_solve_mme")
        
        type(c_ptr), intent(in), value :: c_ptr_in, rhs_ptr, sol_ptr
        integer(c_int), intent(in), value :: dim, max_iter
        real(c_double), intent(in), value :: tol
        integer(c_int) :: iterations
        
        real(c_double), pointer :: C(:,:), rhs(:), solution(:)
        
        call c_f_pointer(c_ptr_in, C, [dim, dim])
        call c_f_pointer(rhs_ptr, rhs, [dim])
        call c_f_pointer(sol_ptr, solution, [dim])
        
        iterations = solve_mme(C, rhs, solution, dim, tol, max_iter)
        
    end function c_solve_mme

end module c_interface
