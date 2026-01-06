# ============================================================================
# Bijmantra Fortran Compute Engine
# CMake Build Configuration
#
# Aerospace-Grade Numerical Precision for Plant Breeding
# ============================================================================

cmake_minimum_required(VERSION 3.15)
project(bijmantra_fortran 
    VERSION 1.0.0-beta.1
    LANGUAGES Fortran C
    DESCRIPTION "High-performance genomic computations for Bijmantra"
)

# ============================================================================
# Build Options
# ============================================================================
option(BUILD_SHARED_LIBS "Build shared libraries" ON)
option(USE_OPENMP "Enable OpenMP parallelization" ON)
option(USE_MKL "Use Intel MKL instead of OpenBLAS" OFF)
option(BUILD_TESTS "Build test suite" ON)

# ============================================================================
# Compiler Settings
# ============================================================================
set(CMAKE_Fortran_MODULE_DIRECTORY ${CMAKE_BINARY_DIR}/modules)

# Fortran compiler flags
if(CMAKE_Fortran_COMPILER_ID MATCHES "GNU")
    set(CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -ffree-form -std=f2018")
    set(CMAKE_Fortran_FLAGS_DEBUG "-g -O0 -Wall -Wextra -fcheck=all -fbacktrace")
    set(CMAKE_Fortran_FLAGS_RELEASE "-O3 -march=native -funroll-loops -flto")
elseif(CMAKE_Fortran_COMPILER_ID MATCHES "Intel")
    set(CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -free -stand f18")
    set(CMAKE_Fortran_FLAGS_DEBUG "-g -O0 -warn all -check all -traceback")
    set(CMAKE_Fortran_FLAGS_RELEASE "-O3 -xHost -ipo")
endif()

# ============================================================================
# Find Dependencies
# ============================================================================

# BLAS/LAPACK
if(USE_MKL)
    find_package(MKL REQUIRED)
    set(BLAS_LAPACK_LIBS MKL::MKL)
else()
    find_package(BLAS REQUIRED)
    find_package(LAPACK REQUIRED)
    set(BLAS_LAPACK_LIBS ${LAPACK_LIBRARIES} ${BLAS_LIBRARIES})
endif()

# OpenMP
if(USE_OPENMP)
    find_package(OpenMP)
    if(OpenMP_Fortran_FOUND)
        set(CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} ${OpenMP_Fortran_FLAGS}")
    endif()
endif()

# ============================================================================
# Source Files
# ============================================================================
set(FORTRAN_SOURCES
    src/blup_solver.f90
    src/kinship.f90
    src/reml_engine.f90
    src/pca_svd.f90
    src/ld_analysis.f90
    src/gxe_analysis.f90
    src/stability_analysis.f90
    src/selection_index.f90
)

# ============================================================================
# Library Target
# ============================================================================
add_library(bijmantra_compute ${FORTRAN_SOURCES})

target_link_libraries(bijmantra_compute
    PUBLIC ${BLAS_LAPACK_LIBS}
)

target_include_directories(bijmantra_compute
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_BINARY_DIR}/modules>
        $<INSTALL_INTERFACE:include>
)

set_target_properties(bijmantra_compute PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION 0
    POSITION_INDEPENDENT_CODE ON
    Fortran_MODULE_DIRECTORY ${CMAKE_BINARY_DIR}/modules
)

# ============================================================================
# C Interface Library (for Rust FFI)
# ============================================================================
add_library(bijmantra_compute_c SHARED
    src/c_interface.f90
)

target_link_libraries(bijmantra_compute_c
    PRIVATE bijmantra_compute
)

set_target_properties(bijmantra_compute_c PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION 0
    C_VISIBILITY_PRESET hidden
)

# ============================================================================
# Tests
# ============================================================================
if(BUILD_TESTS)
    enable_testing()
    
    add_executable(test_blup tests/test_blup.f90)
    target_link_libraries(test_blup bijmantra_compute)
    add_test(NAME test_blup COMMAND test_blup)
    
    add_executable(test_kinship tests/test_kinship.f90)
    target_link_libraries(test_kinship bijmantra_compute)
    add_test(NAME test_kinship COMMAND test_kinship)
    
    add_executable(test_reml tests/test_reml.f90)
    target_link_libraries(test_reml bijmantra_compute)
    add_test(NAME test_reml COMMAND test_reml)
endif()

# ============================================================================
# Installation
# ============================================================================
include(GNUInstallDirs)

install(TARGETS bijmantra_compute bijmantra_compute_c
    EXPORT bijmantra_compute_targets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

install(DIRECTORY ${CMAKE_BINARY_DIR}/modules/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/bijmantra
    FILES_MATCHING PATTERN "*.mod"
)

install(EXPORT bijmantra_compute_targets
    FILE bijmantra_compute_targets.cmake
    NAMESPACE bijmantra::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/bijmantra_compute
)

# ============================================================================
# Package Configuration
# ============================================================================
include(CMakePackageConfigHelpers)

configure_package_config_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/cmake/bijmantra_compute_config.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/bijmantra_compute_config.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/bijmantra_compute
)

write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/bijmantra_compute_config_version.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)

install(FILES
    ${CMAKE_CURRENT_BINARY_DIR}/bijmantra_compute_config.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/bijmantra_compute_config_version.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/bijmantra_compute
)

# ============================================================================
# Summary
# ============================================================================
message(STATUS "")
message(STATUS "Bijmantra Fortran Compute Engine Configuration:")
message(STATUS "  Version:        ${PROJECT_VERSION}")
message(STATUS "  Fortran:        ${CMAKE_Fortran_COMPILER_ID} ${CMAKE_Fortran_COMPILER_VERSION}")
message(STATUS "  Build type:     ${CMAKE_BUILD_TYPE}")
message(STATUS "  OpenMP:         ${OpenMP_Fortran_FOUND}")
message(STATUS "  BLAS/LAPACK:    ${USE_MKL}")
message(STATUS "  Build tests:    ${BUILD_TESTS}")
message(STATUS "")
