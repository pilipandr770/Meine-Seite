"""Print ProductImage rows and product.image links for quick inspection"""
import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.app import create_app
from app.models.product import ProductImage, Product


def main():
    app = create_app()
    with app.app_context():
        imgs = ProductImage.query.order_by(ProductImage.id).all()
        print('Total ProductImage rows:', len(imgs))
        for im in imgs:
            print('id:', im.id, 'product_id:', im.product_id, 'filename:', getattr(im, 'filename', None), 'has_data:', bool(getattr(im, 'data', None)), 'url:', getattr(im, 'url', None))

        prods = Product.query.order_by(Product.id).all()
        print('\nProducts and product.image field:')
        for p in prods:
            print('product id:', p.id, 'name:', p.name, 'image:', p.image)

if __name__ == '__main__':
    try:
        main()
    except Exception:
        import traceback
        print('Exception in print_images:')
        traceback.print_exc()
        raise
