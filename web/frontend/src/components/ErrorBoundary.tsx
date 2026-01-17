import React, { Component, ReactNode } from 'react'

interface Props {
    children: ReactNode
}

interface State {
    hasError: boolean
    error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props)
        this.state = { hasError: false, error: null }
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error }
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('ErrorBoundary caught an error:', error)
        console.error('Error info:', errorInfo)
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{
                    minHeight: '100vh',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: '#1a1a2e',
                    padding: '20px',
                    fontFamily: 'Arial, sans-serif'
                }}>
                    <div style={{
                        backgroundColor: '#16213e',
                        border: '1px solid #e94560',
                        borderRadius: '10px',
                        padding: '30px',
                        maxWidth: '600px',
                        color: '#f3f4f6'
                    }}>
                        <h1 style={{ color: '#e94560', marginBottom: '15px' }}>Something went wrong</h1>
                        <p style={{ marginBottom: '20px', color: '#888' }}>
                            An error occurred while rendering the application.
                        </p>
                        <pre style={{
                            backgroundColor: '#0f3460',
                            padding: '15px',
                            borderRadius: '5px',
                            overflow: 'auto',
                            fontSize: '12px',
                            color: '#ffcccc',
                            marginBottom: '20px'
                        }}>
                            {this.state.error?.toString()}
                        </pre>
                        <button
                            onClick={() => window.location.reload()}
                            style={{
                                backgroundColor: '#e94560',
                                color: 'white',
                                border: 'none',
                                padding: '10px 20px',
                                borderRadius: '5px',
                                cursor: 'pointer',
                                fontSize: '14px'
                            }}
                        >
                            Reload Page
                        </button>
                    </div>
                </div>
            )
        }

        return this.props.children
    }
}
