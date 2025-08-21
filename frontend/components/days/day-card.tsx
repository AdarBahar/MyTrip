/**
 * Day Card Component
 * Displays a single day with date, status, and actions
 */

'use client';

import React from 'react';
import { Day } from '@/types';
import { 
  getDayDisplayDate, 
  getDayDateWithWeekday, 
  getRelativeDayDescription,
  getDayTimeStatus 
} from '@/lib/date-utils';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Calendar,
  MapPin,
  Moon,
  MoreVertical,
  Edit,
  Trash2
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface DayCardProps {
  day: Day;
  onEdit?: (day: Day) => void;
  onDelete?: (day: Day) => void;
  onToggleRestDay?: (day: Day) => void;
  onClick?: (day: Day) => void;
  className?: string;
}

export function DayCard({ 
  day, 
  onEdit, 
  onDelete, 
  onToggleRestDay,
  onClick,
  className = '' 
}: DayCardProps) {
  const displayDate = getDayDisplayDate(day, { format: 'medium', showYear: false });
  const dateWithWeekday = getDayDateWithWeekday(day);
  const relativeDay = day.calculated_date ? getRelativeDayDescription(new Date(day.calculated_date)) : null;
  const timeStatus = getDayTimeStatus(day);

  const handleCardClick = () => {
    if (onClick) {
      onClick(day);
    }
  };

  const getTimeStatusColor = () => {
    switch (timeStatus) {
      case 'past': return 'text-gray-500';
      case 'present': return 'text-blue-600 font-semibold';
      case 'future': return 'text-gray-900';
      default: return 'text-gray-600';
    }
  };

  return (
    <Card 
      className={`transition-all duration-200 hover:shadow-md ${
        onClick ? 'cursor-pointer hover:bg-gray-50' : ''
      } ${className}`}
      onClick={handleCardClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Calendar className="h-4 w-4 text-gray-500" />
              <span className="font-semibold text-lg">Day {day.seq}</span>
            </div>
            
            {day.rest_day && (
              <Badge variant="secondary" className="flex items-center space-x-1">
                <Moon className="h-3 w-3" />
                <span>Rest Day</span>
              </Badge>
            )}
            
            {day.status === 'inactive' && (
              <Badge variant="outline">Inactive</Badge>
            )}
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {onEdit && (
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onEdit(day); }}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit Day
                </DropdownMenuItem>
              )}
              {onToggleRestDay && (
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onToggleRestDay(day); }}>
                  <Moon className="mr-2 h-4 w-4" />
                  {day.rest_day ? 'Remove Rest Day' : 'Mark as Rest Day'}
                </DropdownMenuItem>
              )}
              {onEdit && onDelete && <DropdownMenuSeparator />}
              {onDelete && (
                <DropdownMenuItem 
                  onClick={(e) => { e.stopPropagation(); onDelete(day); }}
                  className="text-red-600"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete Day
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-3">
          {/* Date Information */}
          <div className="space-y-1">
            {displayDate ? (
              <>
                <p className={`text-sm font-medium ${getTimeStatusColor()}`}>
                  {dateWithWeekday}
                </p>
                {relativeDay && (
                  <p className="text-xs text-gray-500">
                    {relativeDay}
                  </p>
                )}
              </>
            ) : (
              <p className="text-sm text-gray-500 italic">
                No date set for trip
              </p>
            )}
          </div>

          {/* Notes Preview */}
          {day.notes && Object.keys(day.notes).length > 0 && (
            <div className="space-y-1">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Notes</p>
              <div className="text-sm text-gray-700">
                {day.notes.description && (
                  <p className="line-clamp-2">{day.notes.description}</p>
                )}
                {day.notes.activities && Array.isArray(day.notes.activities) && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {day.notes.activities.slice(0, 3).map((activity: string, index: number) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {activity}
                      </Badge>
                    ))}
                    {day.notes.activities.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{day.notes.activities.length - 3} more
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Placeholder for stops/routes when implemented */}
          <div className="flex items-center space-x-4 text-xs text-gray-500">
            <div className="flex items-center space-x-1">
              <MapPin className="h-3 w-3" />
              <span>0 stops</span>
            </div>
            {/* Future: Add route info */}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
