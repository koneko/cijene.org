from datetime import datetime
from urllib.parse import urlencode

from loguru import logger

from cijeneorg.fetchers.archiver import WaybackArchiver, PriceList
from cijeneorg.fetchers.common import get_csv_rows, resolve_product, xpath, ensure_archived, extract_offers_from_today
from cijeneorg.models import Store
from cijeneorg.utils import fix_address, fix_city


def fetch_ntl_prices(ntl: Store):
    # comments in the HTML suggest that someone is working on it: https://ibb.co/Vdr4LT0
    WaybackArchiver.archive(index_url := 'https://www.ntl.hr/cjenici-za-ntl-supermarkete')

    # extract both today's hrefs and the archive hrefs and parse them in the same way
    hrefs, root0 = xpath(index_url, '//a[contains(@href, ".csv")]/@href', return_root=True)
    page_name ,= root0.xpath('//input[@name="pageName"]/@value')
    for opt in root0.xpath('//select[@name="archive_file_name"]/option[@value]/@value'):
        _url = index_url + '?' + urlencode({'pageName': page_name, 'archive_file_name': opt})
        WaybackArchiver.archive(_url)
        hrefs.extend(xpath(_url,'//a[contains(@href, ".csv")]/@href'))

    coll = []
    for href in hrefs:
        filename = href.rsplit('/', 1)[-1]
        market_type, address, city, location_id, file_id, rest = filename.split('_', 5)
        if not (location_id.isdigit() and len(location_id) == 5):
            print(f'failed to parse {filename}')
            continue
        dt = datetime.strptime(rest, '%d%m%Y_%H_%M_%S.csv')
        city = fix_city(city)
        address = fix_address(address).replace('Galoviaa', 'Galovića')
        coll.append(PriceList(href, address, city, ntl.id, location_id, dt, filename))

    today_coll = extract_offers_from_today(ntl, coll)

    prod = []
    for p in today_coll:
        rows = get_csv_rows(ensure_archived(p, True, wayback=False))
        for k in rows[1:]:
            name, _id, brand, _qty,  units, mpc, ppu, discount_mpc, last_30d_mpc, may2_price, barcode, category = k
            resolve_product(prod, barcode, ntl, p.location_id, name, discount_mpc or mpc, _qty, may2_price)

    return prod