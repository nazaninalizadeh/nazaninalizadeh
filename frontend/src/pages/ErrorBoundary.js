import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-8">
          <div className="max-w-2xl w-full bg-white rounded-xl border border-red-200 p-8">
            <h1 className="text-2xl font-semibold text-red-900 mb-4">
              Qualcosa è andato storto
            </h1>
            <div className="bg-red-50 p-4 rounded-lg mb-4">
              <p className="text-sm font-mono text-red-800">
                {this.state.error && this.state.error.toString()}
              </p>
            </div>
            <details className="mb-4">
              <summary className="cursor-pointer text-sm font-medium text-slate-700 mb-2">
                Error Details
              </summary>
              <pre className="text-xs bg-slate-100 p-4 rounded overflow-auto max-h-64">
                {this.state.errorInfo && this.state.errorInfo.componentStack}
              </pre>
            </details>
            <button
              onClick={() => window.location.href = '/login'}
              className="px-4 py-2 bg-rose-700 text-white rounded-lg hover:bg-rose-800"
            >
              Vai al Login
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
