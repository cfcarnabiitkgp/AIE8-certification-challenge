import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Research Paper Peer Review',
  description: 'AI-powered peer review for technical research papers',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

