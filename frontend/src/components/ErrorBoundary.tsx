import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI matching website theme
      return (
        <div className="min-h-screen bg-[#FDFCF0] flex items-center justify-center px-4 py-8">
          <div className="max-w-2xl w-full">
            <div className="bg-white rounded-3xl border-2 border-[#1A1A1A] shadow-xl p-8 sm:p-12">
              {/* Error Icon */}
              <div className="flex justify-center mb-6">
                <div className="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center">
                  <AlertTriangle className="w-10 h-10 text-red-600" />
                </div>
              </div>

              {/* Error Message */}
              <h1 className="font-['Baskervville',serif] text-3xl sm:text-4xl text-[#1A1A1A] text-center mb-4">
                Something Went Wrong
              </h1>
              
              <p className="text-[#8A8A8A] text-center mb-8">
                We encountered an unexpected error. Don't worry, your work is safe.
              </p>

              {/* Error Details (collapsible in production) */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mb-8 bg-[#FDFCF0] rounded-xl p-4 border border-[#1A1A1A]/10">
                  <summary className="cursor-pointer font-semibold text-sm text-[#1A1A1A] mb-2">
                    Error Details (Development Mode)
                  </summary>
                  <div className="mt-4 space-y-2">
                    <div className="text-xs font-mono bg-red-50 p-3 rounded-lg border border-red-200 overflow-auto">
                      <strong className="text-red-700">Error:</strong>
                      <pre className="mt-1 text-red-600 whitespace-pre-wrap">
                        {this.state.error.toString()}
                      </pre>
                    </div>
                    {this.state.errorInfo && (
                      <div className="text-xs font-mono bg-gray-50 p-3 rounded-lg border border-gray-200 overflow-auto max-h-64">
                        <strong className="text-gray-700">Component Stack:</strong>
                        <pre className="mt-1 text-gray-600 whitespace-pre-wrap">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>
              )}

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={this.handleReset}
                  className="px-6 py-3 rounded-xl font-semibold text-sm bg-[#1A1A1A] text-white hover:bg-[#2A2A2A] transition-all flex items-center justify-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </button>
                <button
                  onClick={this.handleGoHome}
                  className="px-6 py-3 rounded-xl font-semibold text-sm bg-white border-2 border-[#1A1A1A]/20 text-[#1A1A1A] hover:border-[#1A1A1A] transition-all flex items-center justify-center gap-2"
                >
                  <Home className="w-4 h-4" />
                  Go Home
                </button>
              </div>

              {/* Help Text */}
              <p className="text-xs text-[#8A8A8A] text-center mt-8">
                If this problem persists, please check the console for more details or contact support.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
