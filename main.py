import requests
from lxml import etree
import re

# Ссылка на файл заказчика
url = "https://ouggi.ru/yxml_ss4c2cuh54.xml"


def create_avito_feed():
    print("🚀 Скачиваю базу данных сайта...")
    response = requests.get(url)
    root = etree.fromstring(response.content)
    offers = root.xpath(".//offer")

    # Создаем структуру для Авито
    avito_root = etree.Element("Ads", target="Avito.ru", formatVersion="3")

    # Сюда будем записывать названия моделей, которые мы уже обработали, чтобы убрать дубли
    seen_models = set()

    count_added = 0
    count_skipped_stock = 0
    count_skipped_duplicate = 0

    print(f"🔄 Всего в файле позиций: {len(offers)}. Начинаю фильтрацию...")

    for offer in offers:
        # 1. ФИЛЬТР: Проверяем наличие (available="true")
        # Если товара нет в наличии - пропускаем его
        if offer.get("available") != "true":
            count_skipped_stock += 1
            continue

        # Получаем название модели
        model_name = offer.findtext("model")

        # 2. ГРУППИРОВКА: Проверяем дубли
        # Если мы уже добавили товар с таким названием - пропускаем (это просто другой размер)
        if model_name in seen_models:
            count_skipped_duplicate += 1
            continue

        # Если модель новая и есть в наличии - добавляем её в список "виденных" и создаем объявление
        seen_models.add(model_name)
        count_added += 1

        # --- Создаем блок объявления для Авито ---
        ad = etree.SubElement(avito_root, "Ad")

        # ID (используем ID из файла заказчика)
        etree.SubElement(ad, "Id").text = offer.get("id")

        # Заголовки и Цена
        etree.SubElement(ad, "Title").text = model_name
        etree.SubElement(ad, "Price").text = offer.findtext("price")

        # Описание (чистим от HTML тегов)
        raw_desc = offer.findtext("description") or ""
        clean_desc = re.sub('<[^<]+?>', '', raw_desc).replace("&nbsp;", " ").strip()
        etree.SubElement(ad, "Description").text = clean_desc

        # Адрес (Заказчик сказал Москва)
        etree.SubElement(ad, "Address").text = "Москва"

        # Категория (Одежда)
        etree.SubElement(ad, "Category").text = "Одежда, обувь, аксессуары"
        etree.SubElement(ad, "GoodsType").text = "Женская обувь"
        etree.SubElement(ad, "Condition").text = "Новое"

        # Картинки
        pics = offer.findall("picture")
        if pics:
            images_node = etree.SubElement(ad, "Images")
            # Берем до 10 фоток (Авито разрешает много)
            for pic in pics[:10]:
                etree.SubElement(images_node, "Image", url=pic.text)

    # Сохраняем результат
    tree = etree.ElementTree(avito_root)
    tree.write("avito_feed.xml", encoding="utf-8", xml_declaration=True, pretty_print=True)

    print("-" * 30)
    print(f"❌ Пропущено (нет в наличии): {count_skipped_stock}")
    print(f"❌ Пропущено (дубликаты размеров): {count_skipped_duplicate}")
    print(f"✅ УСПЕШНО ДОБАВЛЕНО: {count_added} товаров")
    print("-" * 30)
    print("Файл avito_feed.xml готов!")


if __name__ == "__main__":
    create_avito_feed()