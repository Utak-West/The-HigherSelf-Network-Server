import React, { createContext, useContext, useEffect, useState } from 'react';

// Create context
const ThemeContext = createContext();

// Provider component
export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');
  const [systemTheme, setSystemTheme] = useState('light');

  // Initialize theme from localStorage or system preference
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    
    setSystemTheme(systemPreference);
    
    if (savedTheme) {
      setTheme(savedTheme);
    } else {
      setTheme(systemPreference);
    }
  }, []);

  // Listen for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e) => {
      const newSystemTheme = e.matches ? 'dark' : 'light';
      setSystemTheme(newSystemTheme);
      
      // If user hasn't set a preference, follow system
      const savedTheme = localStorage.getItem('theme');
      if (!savedTheme || savedTheme === 'system') {
        setTheme(newSystemTheme);
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    
    // Remove existing theme classes
    root.classList.remove('light', 'dark');
    
    // Apply current theme
    if (theme === 'system') {
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
  }, [theme, systemTheme]);

  // Toggle between light and dark
  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
  };

  // Set specific theme
  const setThemeMode = (mode) => {
    setTheme(mode);
    localStorage.setItem('theme', mode);
  };

  // Get current effective theme (resolves 'system' to actual theme)
  const getEffectiveTheme = () => {
    return theme === 'system' ? systemTheme : theme;
  };

  // Check if current theme is dark
  const isDark = () => {
    return getEffectiveTheme() === 'dark';
  };

  // Get theme-aware colors
  const getThemeColors = () => {
    const effectiveTheme = getEffectiveTheme();
    
    if (effectiveTheme === 'dark') {
      return {
        background: 'hsl(224 71% 4%)',
        foreground: 'hsl(213 31% 91%)',
        primary: 'hsl(210 40% 98%)',
        primaryForeground: 'hsl(222.2 47.4% 11.2%)',
        secondary: 'hsl(222.2 84% 4.9%)',
        secondaryForeground: 'hsl(210 40% 98%)',
        muted: 'hsl(223 47% 11%)',
        mutedForeground: 'hsl(215.4 16.3% 56.9%)',
        accent: 'hsl(216 34% 17%)',
        accentForeground: 'hsl(210 40% 98%)',
        border: 'hsl(216 34% 17%)',
        input: 'hsl(216 34% 17%)',
        ring: 'hsl(216 34% 17%)'
      };
    } else {
      return {
        background: 'hsl(0 0% 100%)',
        foreground: 'hsl(222.2 47.4% 11.2%)',
        primary: 'hsl(222.2 47.4% 11.2%)',
        primaryForeground: 'hsl(210 40% 98%)',
        secondary: 'hsl(210 40% 96%)',
        secondaryForeground: 'hsl(222.2 47.4% 11.2%)',
        muted: 'hsl(210 40% 96%)',
        mutedForeground: 'hsl(215.4 16.3% 46.9%)',
        accent: 'hsl(210 40% 96%)',
        accentForeground: 'hsl(222.2 47.4% 11.2%)',
        border: 'hsl(214.3 31.8% 91.4%)',
        input: 'hsl(214.3 31.8% 91.4%)',
        ring: 'hsl(215 20.2% 65.1%)'
      };
    }
  };

  // Context value
  const value = {
    theme,
    systemTheme,
    toggleTheme,
    setThemeMode,
    getEffectiveTheme,
    isDark,
    getThemeColors
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

// Custom hook to use theme context
export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

export default ThemeContext;

