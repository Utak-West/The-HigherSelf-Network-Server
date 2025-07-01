import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { organizationAPI } from '../lib/api';

// Initial state
const initialState = {
  organizations: [],
  currentOrganization: null,
  loading: true,
  error: null
};

// Action types
const ORG_ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_ORGANIZATIONS: 'SET_ORGANIZATIONS',
  SET_CURRENT_ORGANIZATION: 'SET_CURRENT_ORGANIZATION',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  UPDATE_ORGANIZATION: 'UPDATE_ORGANIZATION'
};

// Reducer
function organizationReducer(state, action) {
  switch (action.type) {
    case ORG_ACTIONS.SET_LOADING:
      return {
        ...state,
        loading: action.payload
      };

    case ORG_ACTIONS.SET_ORGANIZATIONS:
      return {
        ...state,
        organizations: action.payload,
        loading: false,
        error: null
      };

    case ORG_ACTIONS.SET_CURRENT_ORGANIZATION:
      return {
        ...state,
        currentOrganization: action.payload,
        error: null
      };

    case ORG_ACTIONS.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        loading: false
      };

    case ORG_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null
      };

    case ORG_ACTIONS.UPDATE_ORGANIZATION:
      return {
        ...state,
        organizations: state.organizations.map(org =>
          org.id === action.payload.id ? { ...org, ...action.payload } : org
        ),
        currentOrganization: state.currentOrganization?.id === action.payload.id
          ? { ...state.currentOrganization, ...action.payload }
          : state.currentOrganization
      };

    default:
      return state;
  }
}

// Create context
const OrganizationContext = createContext();

// Provider component
export function OrganizationProvider({ children }) {
  const [state, dispatch] = useReducer(organizationReducer, initialState);
  const { isAuthenticated, user } = useAuth();

  // Load organizations when user is authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      loadOrganizations();
    } else {
      // Reset state when user logs out
      dispatch({ type: ORG_ACTIONS.SET_ORGANIZATIONS, payload: [] });
      dispatch({ type: ORG_ACTIONS.SET_CURRENT_ORGANIZATION, payload: null });
    }
  }, [isAuthenticated, user]);

  // Load current organization from localStorage
  useEffect(() => {
    if (state.organizations.length > 0 && !state.currentOrganization) {
      const savedOrgId = localStorage.getItem('currentOrganizationId');
      if (savedOrgId) {
        const savedOrg = state.organizations.find(org => org.id.toString() === savedOrgId);
        if (savedOrg) {
          dispatch({ type: ORG_ACTIONS.SET_CURRENT_ORGANIZATION, payload: savedOrg });
        } else {
          // If saved org not found, select the first one
          selectOrganization(state.organizations[0]);
        }
      } else if (state.organizations.length === 1) {
        // Auto-select if only one organization
        selectOrganization(state.organizations[0]);
      }
    }
  }, [state.organizations]);

  // Load organizations function
  const loadOrganizations = async () => {
    try {
      dispatch({ type: ORG_ACTIONS.SET_LOADING, payload: true });
      
      const response = await organizationAPI.getUserOrganizations();
      
      dispatch({ 
        type: ORG_ACTIONS.SET_ORGANIZATIONS, 
        payload: response.organizations || [] 
      });
    } catch (error) {
      console.error('Error loading organizations:', error);
      dispatch({ 
        type: ORG_ACTIONS.SET_ERROR, 
        payload: error.message 
      });
    }
  };

  // Select organization function
  const selectOrganization = (organization) => {
    if (!organization) return;

    dispatch({ 
      type: ORG_ACTIONS.SET_CURRENT_ORGANIZATION, 
      payload: organization 
    });

    // Save to localStorage
    localStorage.setItem('currentOrganizationId', organization.id.toString());
  };

  // Switch organization function
  const switchOrganization = async (organizationId) => {
    const organization = state.organizations.find(org => org.id === organizationId);
    if (organization) {
      selectOrganization(organization);
      return organization;
    } else {
      throw new Error('Organization not found');
    }
  };

  // Get organization by ID
  const getOrganizationById = (organizationId) => {
    return state.organizations.find(org => org.id === organizationId);
  };

  // Check if user has permission in current organization
  const hasPermission = (permission) => {
    if (!state.currentOrganization) return false;
    
    const userRole = state.currentOrganization.role;
    
    // Owner has all permissions
    if (userRole === 'owner') return true;
    
    // Define role permissions
    const rolePermissions = {
      admin: ['read', 'write', 'delete', 'manage_users', 'manage_integrations'],
      manager: ['read', 'write', 'manage_team'],
      user: ['read', 'write'],
      viewer: ['read']
    };

    const permissions = rolePermissions[userRole] || [];
    return permissions.includes(permission) || permissions.includes('*');
  };

  // Check if user has specific role
  const hasRole = (role) => {
    if (!state.currentOrganization) return false;
    return state.currentOrganization.role === role;
  };

  // Get user role in current organization
  const getCurrentRole = () => {
    return state.currentOrganization?.role || null;
  };

  // Update organization settings
  const updateOrganization = async (organizationId, updates) => {
    try {
      const response = await organizationAPI.updateOrganization(organizationId, updates);
      
      dispatch({
        type: ORG_ACTIONS.UPDATE_ORGANIZATION,
        payload: { id: organizationId, ...response.organization }
      });

      return response;
    } catch (error) {
      throw error;
    }
  };

  // Create new organization
  const createOrganization = async (organizationData) => {
    try {
      const response = await organizationAPI.createOrganization(organizationData);
      
      // Reload organizations to include the new one
      await loadOrganizations();
      
      return response;
    } catch (error) {
      throw error;
    }
  };

  // Invite user to organization
  const inviteUser = async (email, role = 'user') => {
    if (!state.currentOrganization) {
      throw new Error('No organization selected');
    }

    try {
      const response = await organizationAPI.inviteUser(
        state.currentOrganization.id,
        email,
        role
      );
      return response;
    } catch (error) {
      throw error;
    }
  };

  // Get organization members
  const getOrganizationMembers = async (organizationId = null) => {
    const orgId = organizationId || state.currentOrganization?.id;
    if (!orgId) {
      throw new Error('No organization specified');
    }

    try {
      const response = await organizationAPI.getOrganizationMembers(orgId);
      return response;
    } catch (error) {
      throw error;
    }
  };

  // Clear error function
  const clearError = () => {
    dispatch({ type: ORG_ACTIONS.CLEAR_ERROR });
  };

  // Get organization theme colors
  const getOrganizationTheme = () => {
    if (!state.currentOrganization) return null;

    return {
      primary: state.currentOrganization.primaryColor || '#007bff',
      secondary: state.currentOrganization.secondaryColor || '#6c757d',
      logo: state.currentOrganization.logoUrl
    };
  };

  // Context value
  const value = {
    ...state,
    loadOrganizations,
    selectOrganization,
    switchOrganization,
    getOrganizationById,
    hasPermission,
    hasRole,
    getCurrentRole,
    updateOrganization,
    createOrganization,
    inviteUser,
    getOrganizationMembers,
    getOrganizationTheme,
    clearError
  };

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
}

// Custom hook to use organization context
export function useOrganization() {
  const context = useContext(OrganizationContext);
  if (!context) {
    throw new Error('useOrganization must be used within an OrganizationProvider');
  }
  return context;
}

export default OrganizationContext;

