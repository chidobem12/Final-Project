/// <reference types="@testing-library/jest-dom" />
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MetricCard } from './MetricCard';

describe('MetricCard Component', () => {
    it('renders the title and value correctly', () => {
        render(<MetricCard title="Total Alerts" value={142} />);
        expect(screen.getByText('Total Alerts')).toBeInTheDocument();
        // displayValue will animate from 142 if it is a number, so we use string for strict check
        render(<MetricCard title="String Val" value="ACTIVE" />);
        expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });

    it('renders the subtitle if provided', () => {
        render(<MetricCard title="Test" value={10} subtitle="Test Subtitle" />);
        expect(screen.getByText('Test Subtitle')).toBeInTheDocument();
    });
});
