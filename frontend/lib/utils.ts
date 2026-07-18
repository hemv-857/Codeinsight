import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function isGithubUrl(input: string): boolean {
  return /^https?:\/\/(www\.)?github\.com\/.+/.test(input.trim());
}
