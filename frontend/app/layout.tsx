import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

import './globals.css';
import { Providers } from '@/components/providers';
import { RepoProvider } from '@/components/repo-context';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'CodeInsight',
  description: 'Google Maps for Software Systems.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} font-sans antialiased`}>
        <Providers>
          <RepoProvider>{children}</RepoProvider>
        </Providers>
      </body>
    </html>
  );
}
