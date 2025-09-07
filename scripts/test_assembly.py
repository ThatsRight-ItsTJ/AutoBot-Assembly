#!/usr/bin/env python3
"""
Test script for Phase 4: Assembly Engine

Tests repository cloning, file extraction, code integration, and project generation.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from assembly.repository_cloner import RepositoryCloner
from assembly.file_extractor import FileExtractor
from assembly.code_integrator import CodeIntegrator
from assembly.project_generator import ProjectGenerator, ProjectType
from search.tier1_packages import PackageResult


async def test_repository_cloning():
    """Test repository cloning functionality."""
    print("\n" + "="*60)
    print("TESTING REPOSITORY CLONER")
    print("="*60)
    
    cloner = RepositoryCloner()
    
    # Create test repositories
    test_repos = [
        PackageResult(
            name="requests",
            repository_url="https://github.com/psf/requests",
            description="HTTP library for Python",
            downloads=1000000,
            stars=50000,
            last_updated=datetime.now(),
            license="Apache-2.0",
            quality_score=0.9,
            language="python",
            package_manager="pypi",
            version="2.31.0",
            dependencies_count=5
        ),
        PackageResult(
            name="flask",
            repository_url="https://github.com/pallets/flask",
            description="Web framework for Python",
            downloads=2000000,
            stars=60000,
            last_updated=datetime.now(),
            license="BSD-3-Clause",
            quality_score=0.95,
            language="python",
            package_manager="pypi",
            version="2.3.0",
            dependencies_count=3
        )
    ]
    
    print(f"Testing with {len(test_repos)} repositories...")
    
    # Clone repositories
    clone_results = await cloner.clone_repositories(test_repos)
    
    print(f"\nClone Results:")
    for repo_name, result in clone_results.items():
        print(f"  • {repo_name}: {result.status.value}")
        if result.status.value == 'success':
            print(f"    Path: {result.local_path}")
            print(f"    Branch: {result.branch}")
            print(f"    Size: {result.size_mb:.1f}MB")
            print(f"    Files: {result.file_count}")
        elif result.error_message:
            print(f"    Error: {result.error_message}")
    
    # Print summary
    summary = cloner.get_clone_summary(clone_results)
    print(f"\nSummary:")
    print(f"  Success rate: {summary['success_rate']:.1%}")
    print(f"  Total size: {summary['total_size_mb']:.1f}MB")
    print(f"  Total files: {summary['total_files']}")
    
    return clone_results


async def test_file_extraction(clone_results):
    """Test file extraction functionality."""
    print("\n" + "="*60)
    print("TESTING FILE EXTRACTOR")
    print("="*60)
    
    extractor = FileExtractor()
    
    print(f"Testing with {len(clone_results)} cloned repositories...")
    
    # Extract files
    extraction_results = await extractor.extract_files(
        clone_results, 
        language="python",
        extraction_criteria={
            'include_code': True,
            'include_config': True,
            'include_docs': True,
            'max_files_per_repo': 20
        }
    )
    
    print(f"\nExtraction Results:")
    for repo_name, result in extraction_results.items():
        print(f"  • {repo_name}: {result.status.value}")
        print(f"    Files found: {result.total_files_found}")
        print(f"    Files extracted: {result.files_extracted}")
        print(f"    Files skipped: {result.files_skipped}")
        print(f"    Extraction path: {result.extraction_path}")
        
        if result.extracted_files:
            print(f"    Top extracted files:")
            for extracted_file in result.extracted_files[:5]:
                print(f"      • {extracted_file.original_path} ({extracted_file.file_type})")
                if extracted_file.quality_score:
                    print(f"        Quality: {extracted_file.quality_score:.2f}")
    
    # Print summary
    summary = extractor.get_extraction_summary(extraction_results)
    print(f"\nSummary:")
    print(f"  Extraction rate: {summary['extraction_rate']:.1%}")
    print(f"  File types: {summary['file_type_distribution']}")
    print(f"  Average files per repo: {summary['average_files_per_repo']:.1f}")
    
    return extraction_results


async def test_code_integration(extraction_results):
    """Test code integration functionality."""
    print("\n" + "="*60)
    print("TESTING CODE INTEGRATOR")
    print("="*60)
    
    integrator = CodeIntegrator()
    
    print(f"Testing with {len(extraction_results)} extraction results...")
    
    # Integrate components
    integration_result = await integrator.integrate_components(
        extraction_results, 
        language="python",
        project_name="test_integration"
    )
    
    print(f"\nIntegration Result:")
    print(f"  Status: {integration_result.status.value}")
    print(f"  Integrated files: {len(integration_result.integrated_files)}")
    print(f"  Generated files: {len(integration_result.generated_files)}")
    print(f"  Import conflicts: {len(integration_result.import_conflicts)}")
    print(f"  Config conflicts: {len(integration_result.config_conflicts)}")
    print(f"  Integration path: {integration_result.integration_path}")
    
    if integration_result.integrated_files:
        print(f"\nIntegrated Files:")
        for file_path in integration_result.integrated_files[:10]:
            print(f"    • {file_path}")
    
    if integration_result.generated_files:
        print(f"\nGenerated Files:")
        for file_path in integration_result.generated_files:
            print(f"    • {file_path}")
    
    if integration_result.import_conflicts:
        print(f"\nImport Conflicts:")
        for conflict in integration_result.import_conflicts:
            print(f"  • {conflict.module_name}: {conflict.conflict_type}")
            print(f"    Files: {', '.join(conflict.conflicting_files)}")
            print(f"    Suggestion: {conflict.resolution_suggestion}")
    
    if integration_result.config_conflicts:
        print(f"\nConfig Conflicts:")
        for conflict in integration_result.config_conflicts:
            print(f"  • {conflict.config_key}")
            print(f"    Files: {', '.join(conflict.files)}")
            print(f"    Suggestion: {conflict.resolution_suggestion}")
    
    return integration_result


async def test_project_generation(integration_result):
    """Test project generation functionality."""
    print("\n" + "="*60)
    print("TESTING PROJECT GENERATOR")
    print("="*60)
    
    generator = ProjectGenerator()
    
    print("Testing project generation...")
    
    # Test different project types
    project_types = [
        (ProjectType.APPLICATION, "test_app"),
        (ProjectType.LIBRARY, "test_lib"),
        (ProjectType.WEB_SERVICE, "test_service"),
        (ProjectType.CLI_TOOL, "test_cli")
    ]
    
    generated_projects = []
    
    for project_type, project_name in project_types:
        print(f"\n--- Generating {project_type.value} project: {project_name} ---")
        
        try:
            generated_project = await generator.generate_project(
                integration_result,
                project_name=project_name,
                language="python",
                project_type=project_type
            )
            
            generated_projects.append(generated_project)
            
            print(f"  ✅ Generated successfully!")
            print(f"    Path: {generated_project.project_path}")
            print(f"    Dependencies: {len(generated_project.dependencies)}")
            print(f"    Build commands: {generated_project.build_commands}")
            print(f"    Run commands: {generated_project.run_commands}")
            print(f"    Test commands: {generated_project.test_commands}")
            
            # Show project structure
            print(f"    Structure:")
            print(f"      Entry points: {generated_project.structure.entry_points}")
            print(f"      Source dirs: {generated_project.structure.source_directories}")
            print(f"      Config files: {generated_project.structure.config_files}")
            print(f"      Test dirs: {generated_project.structure.test_directories}")
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    
    return generated_projects


async def test_complete_workflow():
    """Test complete assembly workflow."""
    print("\n" + "="*60)
    print("TESTING COMPLETE ASSEMBLY WORKFLOW")
    print("="*60)
    
    # Initialize all components
    cloner = RepositoryCloner()
    extractor = FileExtractor()
    integrator = CodeIntegrator()
    generator = ProjectGenerator()
    
    # Create test repository
    test_repo = [
        PackageResult(
            name="click",
            repository_url="https://github.com/pallets/click",
            description="Python CLI library",
            downloads=5000000,
            stars=15000,
            last_updated=datetime.now(),
            license="BSD-3-Clause",
            quality_score=0.92,
            language="python",
            package_manager="pypi",
            version="8.1.0",
            dependencies_count=2
        )
    ]
    
    print("Testing complete workflow with Click library...")
    
    try:
        # Step 1: Clone
        print("\n1. Cloning repository...")
        clone_results = await cloner.clone_repositories(test_repo)
        
        # Step 2: Extract
        print("2. Extracting files...")
        extraction_results = await extractor.extract_files(
            clone_results, 
            language="python",
            extraction_criteria={'max_files_per_repo': 15}
        )
        
        # Step 3: Integrate
        print("3. Integrating components...")
        integration_result = await integrator.integrate_components(
            extraction_results, 
            language="python",
            project_name="complete_workflow_test"
        )
        
        # Step 4: Generate
        print("4. Generating final project...")
        generated_project = await generator.generate_project(
            integration_result,
            project_name="complete_workflow_project",
            language="python",
            project_type=ProjectType.CLI_TOOL
        )
        
        print(f"\n✅ Complete workflow successful!")
        print(f"Final project: {generated_project.project_path}")
        print(f"Project type: {generated_project.project_type.value}")
        print(f"Ready to run: {generated_project.run_commands}")
        
        # Cleanup
        await cloner.cleanup_clones(clone_results)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Complete workflow failed: {e}")
        return False


async def run_all_tests():
    """Run all assembly engine tests."""
    print("AUTOBOT ASSEMBLY SYSTEM - PHASE 4 TESTING")
    print("Assembly Engine (Repository Cloner, File Extractor, Code Integrator, Project Generator)")
    print("=" * 100)
    
    tests = [
        ("Repository Cloning", test_repository_cloning),
        ("Complete Workflow", test_complete_workflow)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name} test...")
            
            if test_name == "Repository Cloning":
                clone_results = await test_func()
                
                # Run dependent tests
                print(f"\n🧪 Running File Extraction test...")
                extraction_results = await test_file_extraction(clone_results)
                
                print(f"\n🧪 Running Code Integration test...")
                integration_result = await test_code_integration(extraction_results)
                
                print(f"\n🧪 Running Project Generation test...")
                generated_projects = await test_project_generation(integration_result)
                
                # Cleanup
                cloner = RepositoryCloner()
                await cloner.cleanup_clones(clone_results)
                
                results[test_name] = "✅ PASSED"
                results["File Extraction"] = "✅ PASSED"
                results["Code Integration"] = "✅ PASSED"
                results["Project Generation"] = "✅ PASSED"
                
            else:
                result = await test_func()
                results[test_name] = "✅ PASSED" if result else "❌ FAILED"
            
            print(f"✅ {test_name} test completed successfully")
            
        except Exception as e:
            results[test_name] = f"❌ FAILED: {str(e)}"
            print(f"❌ {test_name} test failed: {e}")
            logging.exception(f"Test {test_name} failed")
    
    # Print summary
    print("\n" + "="*100)
    print("TEST SUMMARY")
    print("="*100)
    
    for test_name, result in results.items():
        print(f"{test_name}: {result}")
    
    passed_tests = len([r for r in results.values() if "PASSED" in r])
    total_tests = len(results)
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All Phase 4 tests passed! Assembly Engine is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the error messages above.")
        return False


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)