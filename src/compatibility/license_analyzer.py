"""
License Analyzer

Comprehensive license analysis for legal compliance and attribution requirements.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import aiohttp


class LicenseType(str, Enum):
    MIT = "MIT"
    APACHE_2_0 = "Apache-2.0"
    GPL_3_0 = "GPL-3.0"
    GPL_2_0 = "GPL-2.0"
    LGPL_3_0 = "LGPL-3.0"
    LGPL_2_1 = "LGPL-2.1"
    BSD_3_CLAUSE = "BSD-3-Clause"
    BSD_2_CLAUSE = "BSD-2-Clause"
    ISC = "ISC"
    UNLICENSE = "Unlicense"
    CC0_1_0 = "CC0-1.0"
    PROPRIETARY = "Proprietary"
    UNKNOWN = "Unknown"


class CompatibilityStatus(str, Enum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    CONDITIONAL = "conditional"
    UNKNOWN = "unknown"


@dataclass
class LicenseInfo:
    license_type: LicenseType
    license_text: Optional[str]
    requires_attribution: bool
    allows_commercial_use: bool
    allows_modification: bool
    allows_distribution: bool
    requires_source_disclosure: bool
    requires_same_license: bool
    confidence_score: float


@dataclass
class LicenseCompatibility:
    license1: LicenseType
    license2: LicenseType
    status: CompatibilityStatus
    reason: str
    conditions: List[str]


@dataclass
class AttributionRequirement:
    component_name: str
    license_type: LicenseType
    copyright_notice: str
    attribution_text: str
    license_url: Optional[str]


@dataclass
class LicenseAnalysis:
    detected_licenses: Dict[str, LicenseInfo]
    compatibility_matrix: List[LicenseCompatibility]
    commercial_use_allowed: bool
    attribution_requirements: List[AttributionRequirement]
    redistribution_requirements: List[str]
    source_disclosure_required: bool
    overall_compliance_status: str
    recommendations: List[str]


class LicenseAnalyzer:
    """Comprehensive license analysis and compliance checking."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # License detection patterns
        self.license_patterns = {
            LicenseType.MIT: [
                r'MIT License',
                r'Permission is hereby granted, free of charge',
                r'MIT\s*$',
                r'mit-license'
            ],
            LicenseType.APACHE_2_0: [
                r'Apache License.*Version 2\.0',
                r'Licensed under the Apache License',
                r'Apache-2\.0',
                r'apache\.org/licenses/LICENSE-2\.0'
            ],
            LicenseType.GPL_3_0: [
                r'GNU GENERAL PUBLIC LICENSE.*Version 3',
                r'GPL-3\.0',
                r'GNU GPL v3',
                r'www\.gnu\.org/licenses/gpl-3\.0'
            ],
            LicenseType.GPL_2_0: [
                r'GNU GENERAL PUBLIC LICENSE.*Version 2',
                r'GPL-2\.0',
                r'GNU GPL v2',
                r'www\.gnu\.org/licenses/gpl-2\.0'
            ],
            LicenseType.BSD_3_CLAUSE: [
                r'BSD 3-Clause',
                r'Redistribution and use in source and binary forms.*3\.',
                r'BSD-3-Clause',
                r'three-clause BSD'
            ],
            LicenseType.BSD_2_CLAUSE: [
                r'BSD 2-Clause',
                r'Redistribution and use in source and binary forms.*2\.',
                r'BSD-2-Clause',
                r'two-clause BSD'
            ],
            LicenseType.ISC: [
                r'ISC License',
                r'Permission to use, copy, modify, and/or distribute',
                r'ISC\s*$'
            ],
            LicenseType.UNLICENSE: [
                r'This is free and unencumbered software',
                r'UNLICENSE',
                r'unlicense\.org'
            ]
        }
        
        # License compatibility matrix
        self.compatibility_matrix = self._build_compatibility_matrix()
        
        # License characteristics
        self.license_characteristics = {
            LicenseType.MIT: {
                'requires_attribution': True,
                'allows_commercial_use': True,
                'allows_modification': True,
                'allows_distribution': True,
                'requires_source_disclosure': False,
                'requires_same_license': False,
                'permissive': True
            },
            LicenseType.APACHE_2_0: {
                'requires_attribution': True,
                'allows_commercial_use': True,
                'allows_modification': True,
                'allows_distribution': True,
                'requires_source_disclosure': False,
                'requires_same_license': False,
                'permissive': True
            },
            LicenseType.GPL_3_0: {
                'requires_attribution': True,
                'allows_commercial_use': True,
                'allows_modification': True,
                'allows_distribution': True,
                'requires_source_disclosure': True,
                'requires_same_license': True,
                'permissive': False
            },
            LicenseType.GPL_2_0: {
                'requires_attribution': True,
                'allows_commercial_use': True,
                'allows_modification': True,
                'allows_distribution': True,
                'requires_source_disclosure': True,
                'requires_same_license': True,
                'permissive': False
            },
            LicenseType.BSD_3_CLAUSE: {
                'requires_attribution': True,
                'allows_commercial_use': True,
                'allows_modification': True,
                'allows_distribution': True,
                'requires_source_disclosure': False,
                'requires_same_license': False,
                'permissive': True
            },
            LicenseType.BSD_2_CLAUSE: {
                'requires_attribution': True,
                'allows_commercial_use': True,
                'allows_modification': True,
                'allows_distribution': True,
                'requires_source_disclosure': False,
                'requires_same_license': False,
                'permissive': True
            },
            LicenseType.ISC: {
                'requires_attribution': True,
                'allows_commercial_use': True,
                'allows_modification': True,
                'allows_distribution': True,
                'requires_source_disclosure': False,
                'requires_same_license': False,
                'permissive': True
            },
            LicenseType.UNLICENSE: {
                'requires_attribution': False,
                'allows_commercial_use': True,
                'allows_modification': True,
                'allows_distribution': True,
                'requires_source_disclosure': False,
                'requires_same_license': False,
                'permissive': True
            }
        }
    
    async def analyze_license_compliance(self, components: List[Any]) -> LicenseAnalysis:
        """
        Comprehensive license analysis across all components.
        
        Args:
            components: List of discovered components
            
        Returns:
            LicenseAnalysis with comprehensive compliance assessment
        """
        
        # Detect licenses for each component
        detected_licenses = {}
        for i, component in enumerate(components):
            component_id = f"component_{i}"
            license_info = await self._detect_component_license(component)
            detected_licenses[component_id] = license_info
        
        # Analyze license compatibility
        compatibility_matrix = self._analyze_license_compatibility(detected_licenses)
        
        # Check commercial use allowance
        commercial_use_allowed = self._check_commercial_use(detected_licenses)
        
        # Generate attribution requirements
        attribution_requirements = self._generate_attribution_requirements(components, detected_licenses)
        
        # Analyze redistribution requirements
        redistribution_requirements = self._analyze_redistribution_requirements(detected_licenses)
        
        # Check source disclosure requirements
        source_disclosure_required = self._check_source_disclosure_requirements(detected_licenses)
        
        # Determine overall compliance status
        overall_compliance_status = self._determine_compliance_status(compatibility_matrix, detected_licenses)
        
        # Generate recommendations
        recommendations = self._generate_compliance_recommendations(
            compatibility_matrix, detected_licenses, overall_compliance_status
        )
        
        return LicenseAnalysis(
            detected_licenses=detected_licenses,
            compatibility_matrix=compatibility_matrix,
            commercial_use_allowed=commercial_use_allowed,
            attribution_requirements=attribution_requirements,
            redistribution_requirements=redistribution_requirements,
            source_disclosure_required=source_disclosure_required,
            overall_compliance_status=overall_compliance_status,
            recommendations=recommendations
        )
    
    async def _detect_component_license(self, component: Any) -> LicenseInfo:
        """Detect license for a single component."""
        
        # Get license text from various sources
        license_text = ""
        license_field = ""
        
        # Check license field
        if hasattr(component, 'license') and component.license:
            license_field = component.license
            license_text += license_field + " "
        
        # Check description
        if hasattr(component, 'description') and component.description:
            license_text += component.description + " "
        
        # Check repository URL for license indicators
        if hasattr(component, 'repository_url') and component.repository_url:
            license_text += component.repository_url + " "
        
        # Try to fetch LICENSE file if it's a repository
        if hasattr(component, 'repository_url') and 'github.com' in (component.repository_url or ""):
            try:
                license_file_content = await self._fetch_license_file(component.repository_url)
                if license_file_content:
                    license_text += license_file_content
            except Exception as e:
                self.logger.debug(f"Could not fetch license file: {e}")
        
        # Detect license type
        detected_license, confidence = self._detect_license_type(license_text)
        
        # Get license characteristics
        characteristics = self.license_characteristics.get(detected_license, {})
        
        return LicenseInfo(
            license_type=detected_license,
            license_text=license_text[:500] if license_text else None,  # Truncate for storage
            requires_attribution=characteristics.get('requires_attribution', True),
            allows_commercial_use=characteristics.get('allows_commercial_use', True),
            allows_modification=characteristics.get('allows_modification', True),
            allows_distribution=characteristics.get('allows_distribution', True),
            requires_source_disclosure=characteristics.get('requires_source_disclosure', False),
            requires_same_license=characteristics.get('requires_same_license', False),
            confidence_score=confidence
        )
    
    def _detect_license_type(self, license_text: str) -> tuple[LicenseType, float]:
        """Detect license type from text with confidence score."""
        
        if not license_text:
            return LicenseType.UNKNOWN, 0.0
        
        license_text_lower = license_text.lower()
        best_match = LicenseType.UNKNOWN
        best_confidence = 0.0
        
        for license_type, patterns in self.license_patterns.items():
            confidence = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, license_text, re.IGNORECASE):
                    matches += 1
                    confidence += 1.0 / len(patterns)
            
            # Boost confidence for exact matches
            if matches > 0:
                confidence = min(1.0, confidence * (1.0 + matches * 0.2))
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = license_type
        
        return best_match, best_confidence
    
    async def _fetch_license_file(self, repository_url: str) -> Optional[str]:
        """Fetch LICENSE file from GitHub repository."""
        
        # Convert GitHub URL to raw content URL
        if 'github.com' not in repository_url:
            return None
        
        # Extract owner/repo from URL
        parts = repository_url.replace('https://github.com/', '').split('/')
        if len(parts) < 2:
            return None
        
        owner, repo = parts[0], parts[1]
        
        # Try common license file names
        license_files = ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'COPYING', 'COPYING.txt']
        
        for license_file in license_files:
            try:
                url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{license_file}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            content = await response.text()
                            return content[:2000]  # Limit size
            except Exception:
                # Try master branch
                try:
                    url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{license_file}"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=5) as response:
                            if response.status == 200:
                                content = await response.text()
                                return content[:2000]
                except Exception:
                    continue
        
        return None
    
    def _build_compatibility_matrix(self) -> Dict[tuple, LicenseCompatibility]:
        """Build license compatibility matrix."""
        
        compatibility_rules = [
            # Permissive licenses are generally compatible with each other
            (LicenseType.MIT, LicenseType.APACHE_2_0, CompatibilityStatus.COMPATIBLE, 
             "Both are permissive licenses", []),
            (LicenseType.MIT, LicenseType.BSD_3_CLAUSE, CompatibilityStatus.COMPATIBLE,
             "Both are permissive licenses", []),
            (LicenseType.APACHE_2_0, LicenseType.BSD_3_CLAUSE, CompatibilityStatus.COMPATIBLE,
             "Both are permissive licenses", []),
            
            # GPL compatibility issues
            (LicenseType.MIT, LicenseType.GPL_3_0, CompatibilityStatus.CONDITIONAL,
             "MIT can be combined with GPL, but result must be GPL", 
             ["Combined work must be licensed under GPL-3.0"]),
            (LicenseType.GPL_2_0, LicenseType.GPL_3_0, CompatibilityStatus.INCOMPATIBLE,
             "GPL-2.0 and GPL-3.0 are incompatible", 
             ["Use GPL-3.0 only or GPL-2.0 only"]),
            (LicenseType.APACHE_2_0, LicenseType.GPL_2_0, CompatibilityStatus.INCOMPATIBLE,
             "Apache-2.0 and GPL-2.0 are incompatible",
             ["Use different components or separate projects"]),
            (LicenseType.APACHE_2_0, LicenseType.GPL_3_0, CompatibilityStatus.CONDITIONAL,
             "Apache-2.0 can be combined with GPL-3.0 but result must be GPL-3.0",
             ["Combined work must be licensed under GPL-3.0"]),
            
            # Proprietary incompatibilities
            (LicenseType.PROPRIETARY, LicenseType.GPL_3_0, CompatibilityStatus.INCOMPATIBLE,
             "Proprietary software cannot be combined with GPL",
             ["Use different license or separate deployment"]),
            (LicenseType.PROPRIETARY, LicenseType.MIT, CompatibilityStatus.CONDITIONAL,
             "Proprietary can use MIT components with attribution",
             ["Must provide attribution for MIT components"]),
        ]
        
        matrix = {}
        for rule in compatibility_rules:
            license1, license2, status, reason, conditions = rule
            
            # Add both directions
            matrix[(license1, license2)] = LicenseCompatibility(
                license1, license2, status, reason, conditions
            )
            matrix[(license2, license1)] = LicenseCompatibility(
                license2, license1, status, reason, conditions
            )
        
        return matrix
    
    def _analyze_license_compatibility(self, detected_licenses: Dict[str, LicenseInfo]) -> List[LicenseCompatibility]:
        """Analyze compatibility between all detected licenses."""
        
        compatibilities = []
        license_types = [info.license_type for info in detected_licenses.values()]
        unique_licenses = list(set(license_types))
        
        # Check each pair of licenses
        for i, license1 in enumerate(unique_licenses):
            for license2 in unique_licenses[i+1:]:
                compatibility = self.compatibility_matrix.get((license1, license2))
                
                if compatibility:
                    compatibilities.append(compatibility)
                else:
                    # Default compatibility for unknown combinations
                    if license1 == license2:
                        continue  # Same license is always compatible
                    
                    # Assume compatible if both are permissive
                    char1 = self.license_characteristics.get(license1, {})
                    char2 = self.license_characteristics.get(license2, {})
                    
                    if char1.get('permissive', False) and char2.get('permissive', False):
                        status = CompatibilityStatus.COMPATIBLE
                        reason = "Both licenses are permissive"
                        conditions = []
                    else:
                        status = CompatibilityStatus.UNKNOWN
                        reason = "Compatibility unknown - manual review required"
                        conditions = ["Review license terms manually"]
                    
                    compatibilities.append(LicenseCompatibility(
                        license1, license2, status, reason, conditions
                    ))
        
        return compatibilities
    
    def _check_commercial_use(self, detected_licenses: Dict[str, LicenseInfo]) -> bool:
        """Check if commercial use is allowed for all components."""
        
        for license_info in detected_licenses.values():
            if not license_info.allows_commercial_use:
                return False
        
        return True
    
    def _generate_attribution_requirements(self, components: List[Any], 
                                         detected_licenses: Dict[str, LicenseInfo]) -> List[AttributionRequirement]:
        """Generate attribution requirements for components that require it."""
        
        requirements = []
        
        for i, (component_id, license_info) in enumerate(detected_licenses.items()):
            if license_info.requires_attribution:
                component = components[i] if i < len(components) else None
                
                component_name = "Unknown"
                if component and hasattr(component, 'name'):
                    component_name = component.name
                elif component and hasattr(component, 'repository'):
                    component_name = component.repository
                
                # Generate copyright notice
                copyright_notice = f"Copyright (c) {component_name}"
                
                # Generate attribution text
                attribution_text = self._generate_attribution_text(component_name, license_info.license_type)
                
                # Get license URL
                license_url = self._get_license_url(license_info.license_type)
                
                requirements.append(AttributionRequirement(
                    component_name=component_name,
                    license_type=license_info.license_type,
                    copyright_notice=copyright_notice,
                    attribution_text=attribution_text,
                    license_url=license_url
                ))
        
        return requirements
    
    def _generate_attribution_text(self, component_name: str, license_type: LicenseType) -> str:
        """Generate attribution text for a component."""
        
        templates = {
            LicenseType.MIT: f"This software includes {component_name}, licensed under the MIT License.",
            LicenseType.APACHE_2_0: f"This software includes {component_name}, licensed under the Apache License 2.0.",
            LicenseType.BSD_3_CLAUSE: f"This software includes {component_name}, licensed under the BSD 3-Clause License.",
            LicenseType.BSD_2_CLAUSE: f"This software includes {component_name}, licensed under the BSD 2-Clause License.",
        }
        
        return templates.get(license_type, f"This software includes {component_name}, licensed under {license_type}.")
    
    def _get_license_url(self, license_type: LicenseType) -> Optional[str]:
        """Get standard URL for license."""
        
        urls = {
            LicenseType.MIT: "https://opensource.org/licenses/MIT",
            LicenseType.APACHE_2_0: "https://www.apache.org/licenses/LICENSE-2.0",
            LicenseType.GPL_3_0: "https://www.gnu.org/licenses/gpl-3.0.html",
            LicenseType.GPL_2_0: "https://www.gnu.org/licenses/gpl-2.0.html",
            LicenseType.BSD_3_CLAUSE: "https://opensource.org/licenses/BSD-3-Clause",
            LicenseType.BSD_2_CLAUSE: "https://opensource.org/licenses/BSD-2-Clause",
        }
        
        return urls.get(license_type)
    
    def _analyze_redistribution_requirements(self, detected_licenses: Dict[str, LicenseInfo]) -> List[str]:
        """Analyze redistribution requirements."""
        
        requirements = []
        
        has_attribution_required = any(info.requires_attribution for info in detected_licenses.values())
        has_source_disclosure = any(info.requires_source_disclosure for info in detected_licenses.values())
        has_same_license = any(info.requires_same_license for info in detected_licenses.values())
        
        if has_attribution_required:
            requirements.append("Must include attribution notices for all components")
        
        if has_source_disclosure:
            requirements.append("Must provide source code when distributing")
        
        if has_same_license:
            requirements.append("Derivative works must use compatible copyleft license")
        
        return requirements
    
    def _check_source_disclosure_requirements(self, detected_licenses: Dict[str, LicenseInfo]) -> bool:
        """Check if source disclosure is required."""
        
        return any(info.requires_source_disclosure for info in detected_licenses.values())
    
    def _determine_compliance_status(self, compatibility_matrix: List[LicenseCompatibility], 
                                   detected_licenses: Dict[str, LicenseInfo]) -> str:
        """Determine overall compliance status."""
        
        # Check for incompatible licenses
        incompatible_count = len([c for c in compatibility_matrix if c.status == CompatibilityStatus.INCOMPATIBLE])
        conditional_count = len([c for c in compatibility_matrix if c.status == CompatibilityStatus.CONDITIONAL])
        unknown_count = len([c for c in compatibility_matrix if c.status == CompatibilityStatus.UNKNOWN])
        
        if incompatible_count > 0:
            return "Non-compliant - Incompatible licenses detected"
        elif unknown_count > 0:
            return "Unknown - Manual review required"
        elif conditional_count > 0:
            return "Conditional - Additional requirements must be met"
        else:
            return "Compliant - All licenses are compatible"
    
    def _generate_compliance_recommendations(self, compatibility_matrix: List[LicenseCompatibility],
                                           detected_licenses: Dict[str, LicenseInfo],
                                           overall_status: str) -> List[str]:
        """Generate compliance recommendations."""
        
        recommendations = []
        
        if "Non-compliant" in overall_status:
            recommendations.append("🚨 Critical: Remove components with incompatible licenses")
            incompatible = [c for c in compatibility_matrix if c.status == CompatibilityStatus.INCOMPATIBLE]
            for comp in incompatible[:3]:  # Show top 3
                recommendations.append(f"   • {comp.license1} and {comp.license2}: {comp.reason}")
        
        if "Unknown" in overall_status:
            recommendations.append("⚠️ Manual review required for unknown license combinations")
        
        if "Conditional" in overall_status:
            recommendations.append("📋 Additional requirements must be met:")
            conditional = [c for c in compatibility_matrix if c.status == CompatibilityStatus.CONDITIONAL]
            for comp in conditional:
                for condition in comp.conditions:
                    recommendations.append(f"   • {condition}")
        
        # Attribution requirements
        attribution_count = len([info for info in detected_licenses.values() if info.requires_attribution])
        if attribution_count > 0:
            recommendations.append(f"📝 {attribution_count} components require attribution notices")
        
        # Source disclosure requirements
        if any(info.requires_source_disclosure for info in detected_licenses.values()):
            recommendations.append("📂 Source code must be made available due to copyleft licenses")
        
        # Commercial use
        if not all(info.allows_commercial_use for info in detected_licenses.values()):
            recommendations.append("💼 Commercial use may be restricted by some licenses")
        
        if not recommendations:
            recommendations.append("✅ All licenses are compatible and compliant")
        
        return recommendations


# Example usage
async def main():
    from ..search.tier1_packages import PackageResult
    from datetime import datetime
    
    analyzer = LicenseAnalyzer()
    
    # Create test components
    test_components = [
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
    
    print("Analyzing license compliance...")
    license_analysis = await analyzer.analyze_license_compliance(test_components)
    
    print(f"\nLicense Analysis Results:")
    print(f"  Overall status: {license_analysis.overall_compliance_status}")
    print(f"  Commercial use allowed: {license_analysis.commercial_use_allowed}")
    print(f"  Source disclosure required: {license_analysis.source_disclosure_required}")
    print(f"  Attribution requirements: {len(license_analysis.attribution_requirements)}")
    
    print(f"\nDetected licenses:")
    for comp_id, license_info in license_analysis.detected_licenses.items():
        print(f"  {comp_id}: {license_info.license_type} (confidence: {license_info.confidence_score:.2f})")
    
    print(f"\nRecommendations:")
    for rec in license_analysis.recommendations:
        print(f"  {rec}")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())