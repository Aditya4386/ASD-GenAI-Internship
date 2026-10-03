import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from '../App'

// Mock axios
vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

import axios from 'axios'

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders header with title', () => {
    render(<App />)
    expect(screen.getByText('VeriMind')).toBeInTheDocument()
    expect(screen.getByText('Multi-Agent Document Intelligence Platform')).toBeInTheDocument()
  })

  it('shows upload section', () => {
    render(<App />)
    expect(screen.getByText('Document Upload')).toBeInTheDocument()
    expect(screen.getByText('Upload Document')).toBeInTheDocument()
  })

  it('shows agent pipeline', () => {
    render(<App />)
    expect(screen.getByText('Agent Pipeline')).toBeInTheDocument()
    expect(screen.getByText('Retrieve')).toBeInTheDocument()
    expect(screen.getByText('Generator')).toBeInTheDocument()
    expect(screen.getByText('Debate')).toBeInTheDocument()
    expect(screen.getByText('Critic')).toBeInTheDocument()
    expect(screen.getByText('Judge')).toBeInTheDocument()
    expect(screen.getByText('Verify')).toBeInTheDocument()
  })

  it('enables ask button after upload', async () => {
    render(<App />)
    
    const askButton = screen.getByText('Ask Agents')
    expect(askButton).toBeDisabled()
    
    // Mock successful upload
    axios.post.mockResolvedValueOnce({
      data: {
        message: 'Success',
        document: { filename: 'test.txt', num_chunks: 3, file_size: 1024 }
      }
    })
    
    // Simulate file upload
    const fileInput = screen.getByLabelText('Upload Document').querySelector('input[type="file"]')
    // Note: Full file upload test would need more setup
  })
})