import type { Metadata } from 'next';

import './globals.css';
import { Providers } from '@/components/providers';

export const metadata: Metadata = {
  title: 'Forge AI',
  description: 'Google Maps for Software Systems.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
