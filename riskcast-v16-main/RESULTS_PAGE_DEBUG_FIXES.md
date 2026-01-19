# Results Page Debug & Fixes

## Issues Fixed

### 1. Empty Data Detection
**Problem**: Adapter không detect khi backend trả về empty object `{}`

**Fix**: Thêm logic kiểm tra empty data trong adapter:
```typescript
const hasData = 
  (data.risk_score !== undefined && data.risk_score !== null) ||
  (data.profile?.score !== undefined && data.profile?.score !== null) ||
  // ... other checks
```

### 2. Empty State UI
**Problem**: UI không hiển thị empty state message khi không có data

**Fix**: Thêm empty state detection và UI trong ResultsPage:
```typescript
const isEmptyData = 
  viewModel.overview.riskScore.score === 0 &&
  viewModel.overview.riskScore.level === 'Unknown' &&
  viewModel.drivers.length === 0 &&
  Object.keys(viewModel.breakdown.factors).length === 0;
```

### 3. Better Error Handling
**Problem**: Error state không có styling và thông báo rõ ràng

**Fix**: Cải thiện error state UI với styling và message rõ ràng hơn

### 4. Debug Logging
**Problem**: Không có cách để debug khi data không đúng

**Fix**: Thêm console.log để debug raw result và normalized result

## Testing

1. **Empty Data**: Khi backend trả về `{}`, UI sẽ hiển thị "No Risk Analysis Data" message
2. **Valid Data**: Khi có data, UI render bình thường
3. **Error**: Khi có lỗi network, UI hiển thị error message với retry button

## Next Steps

1. Run analysis từ Input page để có data
2. Check console logs để xem raw data và normalized data
3. Verify UI hiển thị đúng với data

