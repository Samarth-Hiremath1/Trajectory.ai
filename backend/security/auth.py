"""
Authentication and authorization utilities
"""
import os
import jwt
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from .input_validation import validate_user_id, ValidationError

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Custom authentication error"""
    pass

class AuthorizationError(Exception):
    """Custom authorization error"""
    pass

class SupabaseAuth:
    """Supabase authentication handler"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.supabase_url or not self.supabase_anon_key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        # Client for user operations
        self.supabase: Client = create_client(self.supabase_url, self.supabase_anon_key)
        
        # Admin client for service operations
        if self.supabase_service_key:
            self.supabase_admin: Client = create_client(self.supabase_url, self.supabase_service_key)
        else:
            self.supabase_admin = self.supabase
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token with Supabase
        
        Args:
            token: JWT token to verify
            
        Returns:
            User information from token
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # Verify token with Supabase
            response = self.supabase.auth.get_user(token)
            
            if not response.user:
                raise AuthenticationError("Invalid token")
            
            user_data = {
                "id": response.user.id,
                "email": response.user.email,
                "email_verified": response.user.email_confirmed_at is not None,
                "created_at": response.user.created_at,
                "last_sign_in": response.user.last_sign_in_at,
                "metadata": response.user.user_metadata or {}
            }
            
            return user_data
            
        except Exception as e:
            logger.warning(f"Token verification failed: {str(e)}")
            raise AuthenticationError(f"Token verification failed: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by ID (admin operation)
        
        Args:
            user_id: User ID to lookup
            
        Returns:
            User information or None if not found
        """
        try:
            # Validate user ID format
            user_id = validate_user_id(user_id)
            
            # Use admin client to get user info
            response = self.supabase_admin.auth.admin.get_user_by_id(user_id)
            
            if response.user:
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "email_verified": response.user.email_confirmed_at is not None,
                    "created_at": response.user.created_at,
                    "last_sign_in": response.user.last_sign_in_at,
                    "metadata": response.user.user_metadata or {}
                }
            
            return None
            
        except ValidationError as e:
            logger.warning(f"Invalid user ID format: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to get user by ID: {str(e)}")
            return None
    
    async def check_user_permissions(self, user_id: str, resource_type: str, 
                                   resource_id: str, action: str) -> bool:
        """
        Check if user has permission to perform action on resource
        
        Args:
            user_id: User ID
            resource_type: Type of resource (profile, resume, roadmap, etc.)
            resource_id: ID of the resource
            action: Action to perform (read, write, delete)
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Basic ownership check - users can only access their own resources
            if resource_type in ['profile', 'resume', 'roadmap', 'chat_session', 'task']:
                # For user-owned resources, check if the resource belongs to the user
                return await self._check_resource_ownership(user_id, resource_type, resource_id)
            
            # For other resources, implement specific permission logic
            return False
            
        except Exception as e:
            logger.error(f"Permission check failed: {str(e)}")
            return False
    
    async def _check_resource_ownership(self, user_id: str, resource_type: str, 
                                      resource_id: str) -> bool:
        """Check if user owns the resource"""
        try:
            # Map resource types to table names
            table_mapping = {
                'profile': 'profiles',
                'resume': 'resumes',
                'roadmap': 'roadmaps',
                'chat_session': 'chat_sessions',
                'task': 'tasks'
            }
            
            table_name = table_mapping.get(resource_type)
            if not table_name:
                return False
            
            # Query the resource to check ownership
            result = self.supabase.table(table_name).select("user_id").eq("id", resource_id).execute()
            
            if result.data and len(result.data) > 0:
                resource_user_id = result.data[0]["user_id"]
                return resource_user_id == user_id
            
            return False
            
        except Exception as e:
            logger.error(f"Ownership check failed: {str(e)}")
            return False

# Global auth instance - lazy initialization
supabase_auth = None

def get_supabase_auth():
    """Get or create the global Supabase auth instance"""
    global supabase_auth
    if supabase_auth is None:
        supabase_auth = SupabaseAuth()
    return supabase_auth

# Security scheme for FastAPI
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        User information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        user_data = await supabase_auth.verify_token(credentials.credentials)
        return user_data
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency to get current user ID
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If authentication fails
    """
    user_data = await get_current_user(credentials)
    return user_data["id"]

async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get user information if authenticated, None otherwise
    
    Args:
        request: FastAPI request object
        
    Returns:
        User information or None
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        user_data = await supabase_auth.verify_token(token)
        return user_data
        
    except Exception:
        return None

def require_permission(resource_type: str, action: str = "read"):
    """
    Decorator to require specific permissions
    
    Args:
        resource_type: Type of resource
        action: Action to perform
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user_id and resource_id from function arguments
            user_id = kwargs.get("user_id") or kwargs.get("current_user_id")
            resource_id = kwargs.get("resource_id") or kwargs.get("id")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User authentication required"
                )
            
            if resource_id:
                # Check permissions for specific resource
                has_permission = await supabase_auth.check_user_permissions(
                    user_id, resource_type, resource_id, action
                )
                
                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions"
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

class RoleBasedAccess:
    """Role-based access control"""
    
    # Define roles and their permissions
    ROLES = {
        "user": {
            "permissions": [
                "read_own_profile",
                "write_own_profile",
                "read_own_resume",
                "write_own_resume",
                "read_own_roadmap",
                "write_own_roadmap",
                "read_own_chat",
                "write_own_chat",
                "read_own_tasks",
                "write_own_tasks"
            ]
        },
        "admin": {
            "permissions": [
                "*"  # All permissions
            ]
        }
    }
    
    @staticmethod
    def get_user_role(user_data: Dict[str, Any]) -> str:
        """Get user role from user data"""
        # Check user metadata for role
        metadata = user_data.get("metadata", {})
        role = metadata.get("role", "user")
        
        # Validate role
        if role not in RoleBasedAccess.ROLES:
            role = "user"
        
        return role
    
    @staticmethod
    def has_permission(user_data: Dict[str, Any], permission: str) -> bool:
        """Check if user has specific permission"""
        role = RoleBasedAccess.get_user_role(user_data)
        role_permissions = RoleBasedAccess.ROLES[role]["permissions"]
        
        # Admin has all permissions
        if "*" in role_permissions:
            return True
        
        return permission in role_permissions

def require_role(required_role: str):
    """
    Decorator to require specific role
    
    Args:
        required_role: Required role name
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get current user from dependencies
            current_user = kwargs.get("current_user")
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = RoleBasedAccess.get_user_role(current_user)
            
            # Check if user has required role or higher
            if user_role != required_role and user_role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role}' required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator