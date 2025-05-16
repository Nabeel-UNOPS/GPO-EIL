import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'UNOPS Remote Sensing Tools Impact Data Dashboard',
  description: 'UNOPS Remote Sensing Tools Impact Data Dashboard',
  creator: 'MIT GenAI Lab Team',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
