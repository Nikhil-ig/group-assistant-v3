import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

console.log('main.tsx loaded')

// More robust root element selection
const rootElement = document.getElementById('root')
console.log('root element:', rootElement)
console.log('DOM ready state:', document.readyState)
console.log('Body:', document.body)

if (!rootElement) {
    console.error('Root element not found. Available elements:', document.body.innerHTML)
    throw new Error('Root element not found')
}

try {
    console.log('Creating React root')
    const root = ReactDOM.createRoot(rootElement)
    console.log('React root created:', root)

    root.render(<App />)

    console.log('React app rendered successfully')
    console.log('Root element after render:', rootElement.innerHTML)
} catch (err) {
    console.error('Error rendering app:', err)
    rootElement.innerHTML = `<div style="color: red; padding: 20px;">Error: ${err instanceof Error ? err.message : 'Unknown error'}</div>`
}
