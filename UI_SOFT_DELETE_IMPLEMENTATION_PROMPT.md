# 🎯 UI Implementation Prompt: Day Soft Delete & Cascade Features

## 📋 **Overview**

The backend has been updated with comprehensive soft delete functionality for days and stops. The UI needs to be updated to work with these changes and provide users with proper day deletion options.

## 🔧 **Backend Changes Summary**

### **1. Day Status Changes**
- **Day status values are now UPPERCASE**: `"ACTIVE"`, `"INACTIVE"`, `"DELETED"`
- **Deleted days are filtered from all API responses** (won't appear in GET requests)
- **Day deletion now properly cascades** to soft delete all associated stops

### **2. New API Response Fields**
- **Stops Summary** (`/stops/{trip_id}/stops/summary`) now includes `days` field with active days count
- **Routing Active Summary** (`/routing/days/{day_id}/active-summary`) now includes `status` field

### **3. Soft Delete Behavior**
- **Days**: When deleted, `status` becomes `"DELETED"` and `deleted_at` is set
- **Stops**: When day is deleted, all stops are soft deleted with `deleted_at` timestamp
- **Filtering**: All endpoints automatically filter out deleted records

## 🎨 **UI Implementation Requirements**

### **1. Update Day Status Handling**

**Current Issue**: UI likely expects lowercase status values (`"active"`, `"inactive"`)
**Fix Required**: Update all day status comparisons to use uppercase values

```typescript
// ❌ OLD - Will break
if (day.status === 'active') { ... }

// ✅ NEW - Correct
if (day.status === 'ACTIVE') { ... }

// ✅ BETTER - Case insensitive
if (day.status?.toUpperCase() === 'ACTIVE') { ... }

// ✅ BEST - Use constants
const DAY_STATUS = {
  ACTIVE: 'ACTIVE',
  INACTIVE: 'INACTIVE', 
  DELETED: 'DELETED'
} as const;

if (day.status === DAY_STATUS.ACTIVE) { ... }
```

**Files to Update**:
- Any component that checks `day.status`
- Day filtering logic
- Status display components
- Day creation/update forms

### **2. Implement Day Deletion UI Flow**

**Requirement**: When user clicks delete day, show options dialog with two choices:

```typescript
interface DayDeletionOptions {
  action: 'reorder' | 'rest_day';
  dayId: string;
  tripId: string;
}

// Option 1: Re-order subsequent days
const reorderDays = async (tripId: string, dayId: string) => {
  // 1. Delete the day
  await deleteDayAPI(tripId, dayId);
  
  // 2. Update sequence numbers for subsequent days
  const subsequentDays = getSubsequentDays(dayId);
  const updates = subsequentDays.map(day => ({
    id: day.id,
    data: { seq: day.seq - 1 }
  }));
  
  await bulkUpdateDaysAPI(tripId, { updates });
  
  // 3. Refresh trip data
  await refetchTripData();
};

// Option 2: Mark as rest day
const markAsRestDay = async (tripId: string, dayId: string) => {
  await updateDayAPI(tripId, dayId, { rest_day: true });
  await refetchTripData();
};
```

**UI Components Needed**:

```tsx
interface DayDeletionDialogProps {
  day: Day;
  tripId: string;
  onClose: () => void;
  onComplete: () => void;
}

const DayDeletionDialog: React.FC<DayDeletionDialogProps> = ({ 
  day, tripId, onClose, onComplete 
}) => {
  const hasStops = day.stops_count > 0;
  
  return (
    <Dialog open onClose={onClose}>
      <DialogTitle>Delete Day {day.seq}</DialogTitle>
      <DialogContent>
        {hasStops && (
          <Alert severity="warning">
            This day has {day.stops_count} stops that will be removed.
          </Alert>
        )}
        
        <Typography>Choose how to handle this deletion:</Typography>
        
        <RadioGroup>
          <FormControlLabel 
            value="reorder" 
            control={<Radio />}
            label={
              <Box>
                <Typography variant="subtitle2">Re-order days</Typography>
                <Typography variant="body2" color="text.secondary">
                  Days {day.seq + 1}+ will shift up (Day {day.seq + 1} becomes Day {day.seq})
                  {hasStops && " • All stops will be removed"}
                </Typography>
              </Box>
            }
          />
          <FormControlLabel 
            value="rest_day" 
            control={<Radio />}
            label={
              <Box>
                <Typography variant="subtitle2">Mark as rest day</Typography>
                <Typography variant="body2" color="text.secondary">
                  Keep the day but mark it as a rest day
                  {hasStops && " • All stops will be removed"}
                </Typography>
              </Box>
            }
          />
        </RadioGroup>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleDelete} variant="contained" color="error">
          Delete Day
        </Button>
      </DialogActions>
    </Dialog>
  );
};
```

### **3. Update API Response Handling**

**Stops Summary Response**:
```typescript
interface StopsSummary {
  trip_id: string;
  total_stops: number;
  by_type: Record<string, number>;
  days: number; // ✅ NEW FIELD
}

// Usage example
const { data: summary } = await getStopsSummary(tripId);
console.log(`Trip has ${summary.days} active days and ${summary.total_stops} stops`);
```

**Routing Active Summary Response**:
```typescript
interface DayRouteActiveSummary {
  day_id: string;
  status: string; // ✅ NEW FIELD - "ACTIVE", "INACTIVE", "DELETED"
  start?: any;
  end?: any;
  route_total_km?: number;
  route_total_min?: number;
  route_coordinates?: number[][];
  route_version_id?: string;
}

// Usage example
const { data: routeSummary } = await getRoutingActiveSummary(dayId);
if (routeSummary.status === 'ACTIVE') {
  // Show routing information
}
```

### **4. Error Handling Updates**

**Handle Deleted Days**:
```typescript
// Days that are deleted won't appear in API responses anymore
// But handle edge cases where UI might have stale data

const handleDayNotFound = (error: any) => {
  if (error.status === 404 && error.message?.includes('Day not found')) {
    // Day was likely deleted, refresh the trip data
    refetchTripData();
    showNotification('Day was deleted', 'info');
  }
};
```

### **5. Update Type Definitions**

```typescript
// Update existing types
type DayStatus = 'ACTIVE' | 'INACTIVE' | 'DELETED';

interface Day {
  id: string;
  trip_id: string;
  seq: number;
  status: DayStatus; // ✅ Updated to use uppercase values
  rest_day: boolean;
  notes?: any;
  // ... other fields
}

interface StopsSummary {
  trip_id: string;
  total_stops: number;
  by_type: Record<string, number>;
  days: number; // ✅ NEW FIELD
}

interface DayRouteActiveSummary {
  day_id: string;
  status: string; // ✅ NEW FIELD
  start?: any;
  end?: any;
  route_total_km?: number;
  route_total_min?: number;
  route_coordinates?: number[][];
  route_version_id?: string;
}
```

## 🔍 **Testing Checklist**

### **Functional Testing**
- [ ] Day status displays correctly (ACTIVE/INACTIVE/DELETED)
- [ ] Day deletion shows options dialog
- [ ] Re-order option properly shifts subsequent days
- [ ] Rest day option marks day as rest day and removes stops
- [ ] Stops summary shows correct active days count
- [ ] Routing summary includes day status
- [ ] Deleted days don't appear in day lists
- [ ] Error handling for deleted days works

### **Edge Cases**
- [ ] Deleting last day in trip
- [ ] Deleting first day in trip  
- [ ] Deleting day with many stops
- [ ] Deleting day with no stops
- [ ] Network errors during deletion
- [ ] Concurrent deletion by multiple users

### **UI/UX Testing**
- [ ] Deletion dialog is clear and informative
- [ ] Warning shown when day has stops
- [ ] Loading states during deletion
- [ ] Success/error notifications
- [ ] Proper confirmation before deletion

## 🚀 **Implementation Priority**

1. **High Priority**: Update day status handling (prevents UI breaks)
2. **High Priority**: Implement day deletion dialog
3. **Medium Priority**: Update API response handling for new fields
4. **Low Priority**: Enhanced error handling and edge cases

## 📚 **API Endpoints Reference**

```bash
# Delete day (triggers cascade soft delete)
DELETE /trips/{trip_id}/days/{day_id}

# Update day to rest day
PATCH /trips/{trip_id}/days/{day_id}
Body: { "rest_day": true }

# Bulk update day sequences
PATCH /trips/{trip_id}/days/bulk
Body: { "updates": [{"id": "day_id", "data": {"seq": 1}}] }

# Get stops summary (includes days count)
GET /stops/{trip_id}/stops/summary
Response: { "days": 5, "total_stops": 12, ... }

# Get routing summary (includes status)
GET /routing/days/{day_id}/active-summary  
Response: { "status": "ACTIVE", ... }
```

## ⚠️ **Breaking Changes**

1. **Day status values changed from lowercase to uppercase**
2. **Deleted days no longer appear in API responses**
3. **New required fields in API responses**

Make sure to test thoroughly after implementing these changes!
