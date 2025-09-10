import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import requests

class ValidationStatus(Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass
class APIValidationResult:
    api_endpoint: str
    method: str
    status: ValidationStatus
    message: str
    details: Dict[str, Any]
    suggestions: List[str]
    confidence_score: float

@dataclass
class Context7APIInfo:
    endpoint: str
    method: str
    description: str
    parameters: Dict[str, Any]
    response_schema: Dict[str, Any]
    authentication: Dict[str, Any]
    rate_limit: Dict[str, Any]
    documentation_url: str

class Context7Validator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.context7_endpoint = os.getenv('CONTEXT7_ENDPOINT', 'http://localhost:8080')
        self.api_key = os.getenv('CONTEXT7_API_KEY')
        self.timeout = int(os.getenv('CONTEXT7_TIMEOUT', '30'))
        
        # Cache for API information
        self.api_info_cache = {}
        
        # Common API patterns for validation
        self.common_api_patterns = {
            'rest': {
                'endpoints': ['/api/', '/v1/', '/v2/', '/rest/'],
                'methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
                'headers': ['Content-Type', 'Authorization', 'Accept'],
                'response_codes': [200, 201, 400, 401, 403, 404, 500]
            },
            'graphql': {
                'endpoints': ['/graphql', '/gql'],
                'methods': ['POST'],
                'headers': ['Content-Type', 'Authorization'],
                'response_codes': [200]
            },
            'soap': {
                'endpoints': ['/soap', '/wsdl'],
                'methods': ['POST'],
                'headers': ['Content-Type', 'SOAPAction'],
                'response_codes': [200]
            }
        }
    
    def validate_api_endpoint(self, endpoint: str, method: str, headers: Dict[str, str] = None, 
                           body: Dict[str, Any] = None) -> APIValidationResult:
        """Validate API endpoint using Context7"""
        try:
            # Get API information from Context7
            api_info = self.get_api_info(endpoint, method)
            
            if not api_info:
                return APIValidationResult(
                    api_endpoint=endpoint,
                    method=method,
                    status=ValidationStatus.UNKNOWN,
                    message="Could not retrieve API information from Context7",
                    details={},
                    suggestions=["Verify the endpoint is registered in Context7"],
                    confidence_score=0.0
                )
            
            # Validate the endpoint
            validation_results = []
            
            # 1. Validate endpoint structure
            structure_validation = self.validate_endpoint_structure(endpoint, method, api_info)
            validation_results.append(structure_validation)
            
            # 2. Validate parameters
            if body:
                param_validation = self.validate_parameters(endpoint, method, body, api_info)
                validation_results.append(param_validation)
            
            # 3. Validate headers
            if headers:
                header_validation = self.validate_headers(endpoint, method, headers, api_info)
                validation_results.append(header_validation)
            
            # 4. Validate response expectations
            response_validation = self.validate_response_expectations(endpoint, method, api_info)
            validation_results.append(response_validation)
            
            # 5. Validate security requirements
            security_validation = self.validate_security_requirements(endpoint, method, headers, api_info)
            validation_results.append(security_validation)
            
            # Combine validation results
            overall_result = self.combine_validation_results(validation_results)
            
            return APIValidationResult(
                api_endpoint=endpoint,
                method=method,
                status=overall_result['status'],
                message=overall_result['message'],
                details=overall_result['details'],
                suggestions=overall_result['suggestions'],
                confidence_score=overall_result['confidence_score']
            )
            
        except Exception as e:
            self.logger.error(f"Failed to validate API endpoint {endpoint}: {e}")
            return APIValidationResult(
                api_endpoint=endpoint,
                method=method,
                status=ValidationStatus.FAILED,
                message=f"Validation failed: {str(e)}",
                details={},
                suggestions=["Check API endpoint availability and Context7 connection"],
                confidence_score=0.0
            )
    
    def get_api_info(self, endpoint: str, method: str) -> Optional[Context7APIInfo]:
        """Get API information from Context7"""
        cache_key = f"{endpoint}:{method}"
        
        if cache_key in self.api_info_cache:
            return self.api_info_cache[cache_key]
        
        try:
            # Prepare request to Context7
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}' if self.api_key else None
            }
            
            params = {
                'endpoint': endpoint,
                'method': method
            }
            
            response = requests.get(
                f"{self.context7_endpoint}/api/info",
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                api_info = Context7APIInfo(
                    endpoint=data.get('endpoint', ''),
                    method=data.get('method', ''),
                    description=data.get('description', ''),
                    parameters=data.get('parameters', {}),
                    response_schema=data.get('response_schema', {}),
                    authentication=data.get('authentication', {}),
                    rate_limit=data.get('rate_limit', {}),
                    documentation_url=data.get('documentation_url', '')
                )
                
                # Cache the result
                self.api_info_cache[cache_key] = api_info
                
                return api_info
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get API info from Context7: {e}")
            return None
    
    def validate_endpoint_structure(self, endpoint: str, method: str, api_info: Context7APIInfo) -> Dict[str, Any]:
        """Validate API endpoint structure"""
        result = {
            'status': ValidationStatus.PASSED,
            'message': "Endpoint structure is valid",
            'details': {},
            'suggestions': [],
            'confidence_score': 1.0
        }
        
        # Check if endpoint matches expected patterns
        api_type = self.detect_api_type(endpoint)
        
        if api_type in self.common_api_patterns:
            pattern = self.common_api_patterns[api_type]
            
            # Check if endpoint matches expected patterns
            endpoint_valid = any(pattern['endpoint'] in endpoint for pattern in pattern['endpoints'])
            
            if not endpoint_valid:
                result['status'] = ValidationStatus.WARNING
                result['message'] = "Endpoint structure doesn't match common patterns"
                result['suggestions'].append(f"Consider using standard {api_type} endpoint patterns")
                result['confidence_score'] = 0.5
        
        return result
    
    def detect_api_type(self, endpoint: str) -> str:
        """Detect API type from endpoint"""
        endpoint_lower = endpoint.lower()
        
        if any(pattern in endpoint_lower for pattern in ['/graphql', '/gql']):
            return 'graphql'
        elif any(pattern in endpoint_lower for pattern in ['/soap', '/wsdl']):
            return 'soap'
        elif any(pattern in endpoint_lower for pattern in ['/api/', '/v1/', '/v2/', '/rest/']):
            return 'rest'
        else:
            return 'unknown'
    
    def validate_parameters(self, endpoint: str, method: str, body: Dict[str, Any], api_info: Context7APIInfo) -> Dict[str, Any]:
        """Validate request parameters"""
        result = {
            'status': ValidationStatus.PASSED,
            'message': "Parameters are valid",
            'details': {},
            'suggestions': [],
            'confidence_score': 1.0
        }
        
        # Check if required parameters are present
        if 'required' in api_info.parameters:
            required_params = api_info.parameters['required']
            missing_params = [param for param in required_params if param not in body]
            
            if missing_params:
                result['status'] = ValidationStatus.FAILED
                result['message'] = f"Missing required parameters: {', '.join(missing_params)}"
                result['suggestions'].append(f"Add required parameters: {', '.join(missing_params)}")
                result['confidence_score'] = 0.0
        
        # Check parameter types
        if 'properties' in api_info.parameters:
            properties = api_info.parameters['properties']
            for param_name, param_schema in properties.items():
                if param_name in body:
                    param_value = body[param_name]
                    expected_type = param_schema.get('type', 'string')
                    
                    if not self.validate_parameter_type(param_value, expected_type):
                        result['status'] = ValidationStatus.WARNING
                        result['message'] = f"Parameter '{param_name}' type mismatch"
                        result['suggestions'].append(f"Ensure parameter '{param_name}' is of type {expected_type}")
                        result['confidence_score'] = max(0.0, result['confidence_score'] - 0.3)
        
        return result
    
    def validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type"""
        type_mapping = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        expected_python_type = type_mapping.get(expected_type, str)
        return isinstance(value, expected_python_type)
    
    def validate_headers(self, endpoint: str, method: str, headers: Dict[str, str], api_info: Context7APIInfo) -> Dict[str, Any]:
        """Validate request headers"""
        result = {
            'status': ValidationStatus.PASSED,
            'message': "Headers are valid",
            'details': {},
            'suggestions': [],
            'confidence_score': 1.0
        }
        
        # Check required headers
        api_type = self.detect_api_type(endpoint)
        if api_type in self.common_api_patterns:
            pattern = self.common_api_patterns[api_type]
            
            for required_header in pattern['headers']:
                if required_header not in headers:
                    result['status'] = ValidationStatus.WARNING
                    result['message'] = f"Missing required header: {required_header}"
                    result['suggestions'].append(f"Add header: {required_header}")
                    result['confidence_score'] = max(0.0, result['confidence_score'] - 0.2)
        
        # Check authentication headers
        if api_info.authentication:
            auth_type = api_info.authentication.get('type', 'none')
            
            if auth_type == 'bearer' and 'Authorization' not in headers:
                result['status'] = ValidationStatus.FAILED
                result['message'] = "Missing Authorization header for Bearer token authentication"
                result['suggestions'].append("Add Authorization header with Bearer token")
                result['confidence_score'] = 0.0
            
            elif auth_type == 'api_key' and 'X-API-Key' not in headers:
                result['status'] = ValidationStatus.FAILED
                result['message'] = "Missing X-API-Key header for API key authentication"
                result['suggestions'].append("Add X-API-Key header")
                result['confidence_score'] = 0.0
        
        return result
    
    def validate_response_expectations(self, endpoint: str, method: str, api_info: Context7APIInfo) -> Dict[str, Any]:
        """Validate response expectations"""
        result = {
            'status': ValidationStatus.PASSED,
            'message': "Response expectations are valid",
            'details': {},
            'suggestions': [],
            'confidence_score': 1.0
        }
        
        # Check if method is supported
        if method not in api_info.method:
            result['status'] = ValidationStatus.FAILED
            result['message'] = f"Method {method} not supported for this endpoint"
            result['suggestions'].append(f"Use supported methods: {', '.join(api_info.method)}")
            result['confidence_score'] = 0.0
        
        # Check response schema
        if api_info.response_schema:
            schema_validation = self.validate_response_schema(api_info.response_schema)
            if schema_validation['status'] != ValidationStatus.PASSED:
                result['status'] = schema_validation['status']
                result['message'] = schema_validation['message']
                result['suggestions'].extend(schema_validation['suggestions'])
                result['confidence_score'] = schema_validation['confidence_score']
        
        return result
    
    def validate_response_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate response schema structure"""
        result = {
            'status': ValidationStatus.PASSED,
            'message': "Response schema is valid",
            'details': {},
            'suggestions': [],
            'confidence_score': 1.0
        }
        
        # Basic schema validation
        required_fields = ['type', 'properties']
        for field in required_fields:
            if field not in schema:
                result['status'] = ValidationStatus.WARNING
                result['message'] = f"Missing required field in schema: {field}"
                result['suggestions'].append(f"Add {field} to response schema")
                result['confidence_score'] = max(0.0, result['confidence_score'] - 0.3)
        
        return result
    
    def validate_security_requirements(self, endpoint: str, method: str, headers: Dict[str, str], 
                                     api_info: Context7APIInfo) -> Dict[str, Any]:
        """Validate security requirements"""
        result = {
            'status': ValidationStatus.PASSED,
            'message': "Security requirements are valid",
            'details': {},
            'suggestions': [],
            'confidence_score': 1.0
        }
        
        # Check rate limiting
        if api_info.rate_limit:
            rate_limit = api_info.rate_limit
            if 'requests_per_minute' in rate_limit:
                result['suggestions'].append(f"Rate limit: {rate_limit['requests_per_minute']} requests per minute")
        
        # Check authentication
        if api_info.authentication:
            auth_type = api_info.authentication.get('type', 'none')
            
            if auth_type == 'bearer':
                if 'Authorization' not in headers or not headers['Authorization'].startswith('Bearer '):
                    result['status'] = ValidationStatus.FAILED
                    result['message'] = "Bearer token authentication required"
                    result['suggestions'].append("Add Authorization header with Bearer token")
                    result['confidence_score'] = 0.0
            
            elif auth_type == 'api_key':
                if 'X-API-Key' not in headers:
                    result['status'] = ValidationStatus.FAILED
                    result['message'] = "API key authentication required"
                    result['suggestions'].append("Add X-API-Key header")
                    result['confidence_score'] = 0.0
        
        return result
    
    def combine_validation_results(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine multiple validation results"""
        if not validation_results:
            return {
                'status': ValidationStatus.UNKNOWN,
                'message': "No validation results",
                'details': {},
                'suggestions': [],
                'confidence_score': 0.0
            }
        
        # Determine overall status
        overall_status = ValidationStatus.PASSED
        for result in validation_results:
            if result['status'] == ValidationStatus.FAILED:
                overall_status = ValidationStatus.FAILED
                break
            elif result['status'] == ValidationStatus.WARNING and overall_status != ValidationStatus.FAILED:
                overall_status = ValidationStatus.WARNING
        
        # Combine messages and suggestions
        all_messages = [result['message'] for result in validation_results]
        all_suggestions = []
        for result in validation_results:
            all_suggestions.extend(result['suggestions'])
        
        # Calculate average confidence score
        avg_confidence = sum(result['confidence_score'] for result in validation_results) / len(validation_results)
        
        return {
            'status': overall_status,
            'message': '; '.join(all_messages),
            'details': {result['message']: result['details'] for result in validation_results},
            'suggestions': list(set(all_suggestions)),  # Remove duplicates
            'confidence_score': avg_confidence
        }
    
    def validate_batch_apis(self, api_configs: List[Dict[str, Any]]) -> List[APIValidationResult]:
        """Validate multiple API endpoints"""
        results = []
        
        for config in api_configs:
            result = self.validate_api_endpoint(
                endpoint=config.get('endpoint', ''),
                method=config.get('method', 'GET'),
                headers=config.get('headers', {}),
                body=config.get('body', {})
            )
            results.append(result)
        
        return results
    
    def get_api_documentation(self, endpoint: str, method: str) -> Optional[str]:
        """Get API documentation from Context7"""
        try:
            api_info = self.get_api_info(endpoint, method)
            return api_info.documentation_url if api_info else None
        
        except Exception as e:
            self.logger.error(f"Failed to get API documentation: {e}")
            return None
    
    def clear_cache(self):
        """Clear the API info cache"""
        self.api_info_cache.clear()