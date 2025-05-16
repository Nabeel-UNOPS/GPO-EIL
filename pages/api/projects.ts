import { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    // Fetch data from our FastAPI backend
    const apiUrl = process.env.API_URL || 'http://localhost:8000'
    const response = await fetch(`${apiUrl}/api/projects`)
    
    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`)
    }
    
    const data = await response.json()
    return res.status(200).json(data)
  } catch (error) {
    console.error('Error fetching projects:', error)
    return res.status(500).json({ error: 'Failed to fetch projects' })
  }
}
