import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Building2, ChevronRight, Users, BarChart3 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useOrganization } from '../../hooks/useOrganization';
import LoadingSpinner from '../ui/LoadingSpinner';

const OrganizationSelector = () => {
  const { organizations, selectOrganization, loading } = useOrganization();
  const [selectedOrgId, setSelectedOrgId] = useState(null);

  const handleSelectOrganization = (organization) => {
    setSelectedOrgId(organization.id);
    selectOrganization(organization);
  };

  const getRoleColor = (role) => {
    const colors = {
      owner: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      admin: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      manager: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      user: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
      viewer: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
    };
    return colors[role] || colors.user;
  };

  const getOrganizationIcon = (orgName) => {
    if (orgName.toLowerCase().includes('consulting')) return BarChart3;
    if (orgName.toLowerCase().includes('space')) return Building2;
    if (orgName.toLowerCase().includes('network')) return Users;
    return Building2;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-4xl"
      >
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Select Organization
          </h1>
          <p className="text-muted-foreground">
            Choose which organization you'd like to access
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {organizations.map((org, index) => {
            const IconComponent = getOrganizationIcon(org.name);
            const isSelected = selectedOrgId === org.id;

            return (
              <motion.div
                key={org.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <Card 
                  className={`cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-105 ${
                    isSelected ? 'ring-2 ring-primary shadow-lg' : ''
                  }`}
                  onClick={() => handleSelectOrganization(org)}
                >
                  <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                          <IconComponent className="w-6 h-6 text-primary" />
                        </div>
                        <div>
                          <CardTitle className="text-lg">{org.displayName || org.name}</CardTitle>
                          <CardDescription className="text-sm">
                            {org.slug}
                          </CardDescription>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-muted-foreground" />
                    </div>
                  </CardHeader>
                  
                  <CardContent className="pt-0">
                    <div className="flex items-center justify-between">
                      <Badge className={getRoleColor(org.role)}>
                        {org.role.charAt(0).toUpperCase() + org.role.slice(1)}
                      </Badge>
                      
                      {org.logoUrl && (
                        <img 
                          src={org.logoUrl} 
                          alt={`${org.displayName} logo`}
                          className="w-8 h-8 rounded object-cover"
                        />
                      )}
                    </div>
                    
                    {org.description && (
                      <p className="text-sm text-muted-foreground mt-3 line-clamp-2">
                        {org.description}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>

        {organizations.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="text-center py-12"
          >
            <Building2 className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-foreground mb-2">
              No Organizations Found
            </h3>
            <p className="text-muted-foreground mb-6">
              You don't have access to any organizations yet.
            </p>
            <Button variant="outline">
              Contact Administrator
            </Button>
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mt-8 text-center"
        >
          <p className="text-sm text-muted-foreground">
            Need access to a different organization?{' '}
            <button className="text-primary hover:text-primary/80 transition-colors">
              Request Access
            </button>
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default OrganizationSelector;

