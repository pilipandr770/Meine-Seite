# Update for Blueprint Naming Conflict Fix

This update resolves the blueprint naming conflict that was causing the application to fail on Render.com.

## Changes Made:

1. Renamed the blueprint in `media_routes.py` from `'media'` to `'category_media'` to avoid conflict with the existing media blueprint.

2. Updated URL paths in all related files:
   - Changed `/media/category-image/{id}` to `/category_media/category-image/{id}`
   - Updated references in:
     - `app/routes/category_media.py`
     - `app/routes/admin_shop.py`
     - `app/utils/image_utils.py`
     - `migrate_category_images.py`

3. Updated route endpoint in `category_media.py` to use the `/category-image/{id}` path under the category_media blueprint.

## Testing:

After deploying these changes, verify:
1. Category image uploads work correctly
2. Category images display properly
3. No blueprint conflicts in logs

The error "ValueError: Имя "media" уже зарегистрировано для другой схемы" should be resolved.
