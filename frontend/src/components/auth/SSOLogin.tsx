import React from 'react';
import { Shield, Key, Building } from 'lucide-react';

interface SSOProvider {
  id: string;
  name: string;
  type: 'oidc' | 'saml';
  icon?: React.ReactNode;
}

const AVAILABLE_PROVIDERS: SSOProvider[] = [
  { id: 'google', name: 'Google Workspace', type: 'oidc' },
  { id: 'okta', name: 'Okta SSO', type: 'saml' },
  { id: 'azure', name: 'Azure AD', type: 'saml' },
];

export const SSOLogin: React.FC = () => {
  const handleLogin = (providerId: string) => {
    // Redirect to backend SSO init endpoint
    // In production, base URL should be dynamic
    const backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    window.location.href = `${backendUrl}/api/v2/sso/login/${providerId}?redirect_to=${encodeURIComponent(window.location.pathname)}`;
  };

  return (
    <div className="w-full max-w-md mx-auto p-6 bg-white rounded-xl shadow-sm border border-slate-200">
      <div className="text-center mb-6">
        <div className="w-12 h-12 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <Shield className="w-6 h-6 text-indigo-600" />
        </div>
        <h2 className="text-2xl font-semibold text-slate-900">Single Sign-On</h2>
        <p className="text-slate-500 mt-2">Access your organization workspace</p>
      </div>

      <div className="space-y-3">
        {AVAILABLE_PROVIDERS.map((provider) => (
          <button
            key={provider.id}
            onClick={() => handleLogin(provider.id)}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-slate-200 rounded-lg hover:bg-slate-50 hover:border-slate-300 transition-all group"
          >
            {provider.type === 'oidc' ? (
              <Key className="w-5 h-5 text-slate-400 group-hover:text-indigo-500" />
            ) : (
              <Building className="w-5 h-5 text-slate-400 group-hover:text-indigo-500" />
            )}
            <span className="font-medium text-slate-700">{provider.name}</span>
          </button>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t border-slate-100 text-center">
        <p className="text-xs text-slate-400">
          Protected by Bijmantra Enterprise Security.
          <br />
          Contact your administrator if you need access.
        </p>
      </div>
    </div>
  );
};
