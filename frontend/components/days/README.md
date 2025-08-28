# Days Management System

A comprehensive React component system for managing trip days with dynamic date calculation and full CRUD operations.

## Features

### ✅ Dynamic Date Calculation
- Automatically calculates day dates from trip start date
- Day 1 = trip.start_date, Day 2 = start_date + 1 day, etc.
- Handles trips without start dates gracefully
- Updates automatically when trip dates change

### ✅ Complete CRUD Operations
- Create new days with auto-sequence generation
- Edit day details (sequence, rest day status, notes)
- Delete days with confirmation dialogs
- Toggle rest day status with one click

### ✅ Rich UI Components
- **DayCard**: Individual day display with actions
- **DaysList**: Grid layout with management controls
- **CreateDayDialog**: Form for adding new days
- **EditDayDialog**: Full editing capabilities
- **DeleteDayDialog**: Safe deletion with warnings

## Quick Start

### Basic Usage

```tsx
import { DaysList } from '@/components/days';
import { Trip } from '@/types';

const trip: Trip = {
  id: 'trip-123',
  start_date: '2024-06-15',
  // ... other trip properties
};

function TripDaysPage() {
  const handleDayClick = (day: Day) => {
    // Navigate to day detail or open day editor
    router.push(`/trips/${trip.slug}/days/${day.id}`);
  };

  return (
    <DaysList 
      trip={trip}
      onDayClick={handleDayClick}
    />
  );
}
```

### Individual Components

```tsx
import { DayCard, CreateDayDialog } from '@/components/days';
import { useDays } from '@/hooks/use-days';

function CustomDaysView({ trip }: { trip: Trip }) {
  const { days, createDay, updateDay, deleteDay } = useDays({
    tripId: trip.id
  });

  return (
    <div>
      {days.map(day => (
        <DayCard
          key={day.id}
          day={day}
          onEdit={(day) => setEditingDay(day)}
          onDelete={(day) => setDeletingDay(day)}
          onToggleRestDay={(day) => toggleRestDay(day.id)}
        />
      ))}
    </div>
  );
}
```

## API Integration

### Using the Days Hook

```tsx
import { useDays } from '@/hooks/use-days';

function DaysManager({ tripId }: { tripId: string }) {
  const {
    days,           // Array of Day objects
    loading,        // Loading state
    error,          // Error message
    refetch,        // Refetch function
    createDay,      // Create new day
    updateDay,      // Update existing day
    deleteDay,      // Delete day
    toggleRestDay,  // Toggle rest day status
    addNotes        // Add/update notes
  } = useDays({ tripId });

  // Create a new day
  const handleCreateDay = async () => {
    const newDay = await createDay({
      rest_day: false,
      notes: { description: 'Exploring the city' }
    });
  };

  // Update a day
  const handleUpdateDay = async (dayId: string) => {
    const updatedDay = await updateDay(dayId, {
      rest_day: true,
      notes: { description: 'Rest and relaxation' }
    });
  };

  return (
    <div>
      {loading && <div>Loading days...</div>}
      {error && <div>Error: {error}</div>}
      {days.map(day => (
        <div key={day.id}>
          Day {day.seq}: {day.calculated_date || 'No date'}
        </div>
      ))}
    </div>
  );
}
```

## Date Utilities

### Calculating and Formatting Dates

```tsx
import { 
  getDayDisplayDate, 
  getDayDateWithWeekday,
  getRelativeDayDescription,
  getDayTimeStatus 
} from '@/lib/date-utils';

function DayDateDisplay({ day }: { day: Day }) {
  const displayDate = getDayDisplayDate(day, { 
    format: 'medium', 
    showWeekday: true 
  });
  
  const weekdayDate = getDayDateWithWeekday(day);
  const relativeDay = getRelativeDayDescription(
    day.calculated_date ? new Date(day.calculated_date) : null
  );
  const timeStatus = getDayTimeStatus(day);

  return (
    <div>
      <p>{displayDate}</p>              {/* "Mon, Jun 15" */}
      <p>{weekdayDate}</p>              {/* "Monday, Jun 15" */}
      <p>{relativeDay}</p>              {/* "Today" or "In 3 days" */}
      <p>Status: {timeStatus}</p>       {/* "past", "present", "future" */}
    </div>
  );
}
```

## Data Types

### Day Object Structure

```typescript
interface Day {
  id: string;
  trip_id: string;
  seq: number;                    // Day sequence (1, 2, 3, etc.)
  status: 'active' | 'inactive';
  rest_day: boolean;
  notes: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  
  // Computed fields from API
  trip_start_date: string | null;   // Trip start date for calculation
  calculated_date: string | null;   // Computed date (ISO string)
}
```

### Creating/Updating Days

```typescript
interface DayCreate {
  seq?: number;                     // Auto-generated if not provided
  status?: 'active' | 'inactive';
  rest_day?: boolean;
  notes?: Record<string, any>;
}

interface DayUpdate {
  seq?: number;
  status?: 'active' | 'inactive';
  rest_day?: boolean;
  notes?: Record<string, any>;
}
```

## Styling and Customization

### Custom Styling

```tsx
import { DayCard } from '@/components/days';

function CustomDayCard({ day }: { day: Day }) {
  return (
    <DayCard
      day={day}
      className="custom-day-card shadow-lg hover:shadow-xl"
      // ... other props
    />
  );
}
```

### Theme Integration

The components use Tailwind CSS and shadcn/ui components, making them easy to customize with your design system.

## Error Handling

```tsx
function DaysWithErrorHandling({ tripId }: { tripId: string }) {
  const { days, loading, error, refetch } = useDays({ tripId });

  if (loading) return <DaysLoadingSkeleton />;
  
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load days: {error}
          <Button onClick={refetch} className="ml-2">
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return <DaysList trip={trip} />;
}
```

## Best Practices

1. **Always handle loading and error states**
2. **Use the useDays hook for state management**
3. **Leverage date utilities for consistent formatting**
4. **Implement optimistic UI updates where possible**
5. **Validate sequence numbers to prevent conflicts**
6. **Use TypeScript for type safety**

## Dependencies

- React 18+
- Next.js 13+ (App Router)
- Tailwind CSS
- shadcn/ui components
- React Hook Form
- Zod validation
- date-fns (optional, for advanced date operations)

## Contributing

When adding new features:
1. Update TypeScript types in `/types/index.ts`
2. Add corresponding API functions in `/lib/api/days.ts`
3. Update hooks in `/hooks/use-days.ts`
4. Create/update UI components as needed
5. Add comprehensive tests
