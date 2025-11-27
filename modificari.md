# Modificări Order Service - Parsare Inteligentă

**Data:** 26 Noiembrie 2025
**Fișier modificat:** `app/services/order_service.py`

---

## Problema

Aplicația noastră primește comenzi prin email de la platforma eEatingh. Emailurile conțin date despre client în format HTML, structurate astfel:

```
Adresa de livrare:
[Nume Client]      ← uneori lipsește!
[Telefon]
[Adresă]
[Link vizualizare]
```

### Ce se întâmpla greșit?

Codul vechi presupunea că datele vin **mereu în aceeași ordine**:
- Primul element = Nume
- Al doilea element = Telefon
- Al treilea element = Adresă

```python
# COD VECHI (problematic)
if len(text_tags) >= 3:
    order_data["nume_client"] = text_tags[0]      # Presupune poziția 0 = nume
    order_data["numar_telefon_client"] = text_tags[1]  # Presupune poziția 1 = telefon
    order_data["adresa_livrare_client"] = text_tags[2]  # Presupune poziția 2 = adresă
```

### Exemplu de eroare reală

Pentru comanda #6615, emailul avea numele **gol** (clientul nu și-a completat numele):

```
Adresa de livrare:
[GOL]                    ← Numele lipsea!
0755828064               ← Telefonul
DJ152A 11, Sincraiu...   ← Adresa
Click aici...            ← Link
```

**Rezultat greșit:**
```json
{
  "nume_client": "0755828064",           // ❌ Aici e telefonul!
  "numar_telefon_client": "DJ152A 11...", // ❌ Aici e adresa!
  "adresa_livrare_client": "Click aici..."  // ❌ Aici e un link!
}
```

---

## Soluția

Am înlocuit logica bazată pe **poziție** cu o logică bazată pe **conținut**.

### Ideea principală

În loc să presupunem "primul element e numele", acum **analizăm fiecare element** și determinăm ce reprezintă:

| Element | Cum îl recunoaștem |
|---------|-------------------|
| **Telefon** | Începe cu `07`, `+40`, sau e format doar din 10-12 cifre |
| **Adresă** | Conține cuvinte ca "strada", "bloc", "nr", "Mures", sau are link Google Maps |
| **Nume** | Ce rămâne după ce eliminăm telefonul și adresa (fără cifre, fără virgule) |

---

## Codul nou explicat pas cu pas

### Pasul 1: Definim pattern-uri de recunoaștere

```python
# Pattern pentru numere de telefon românești
phone_pattern = re.compile(r'^(\+?4?0?7\d{8}|\d{10}|\+?\d{11,12})$')
```

**Ce înseamnă acest pattern:**
- `\+?` = poate începe cu + (opțional)
- `4?0?` = poate avea 4 și/sau 0 (pentru +40)
- `7\d{8}` = cifra 7 urmată de exact 8 cifre
- `|\d{10}` = SAU exact 10 cifre
- `|\+?\d{11,12}` = SAU 11-12 cifre (cu + opțional)

**Exemple care se potrivesc:**
- `0755828064` ✅
- `+40749900372` ✅
- `40755123456` ✅

```python
# Pattern pentru cuvinte cheie de adresă
address_keywords_pattern = re.compile(
    r'\b(str\.?|strada|bloc|etaj|ap\.?|nr\.?|judet|oras|municipiu|sat|comuna|sector|'
    r'mures|maros|cluj|bucuresti|timis|brasov|sibiu|alba|principala|calea|bulevardul|'
    r'aleea|piata)\b',
    re.IGNORECASE
)
```

**Important:** Folosim `\b` (word boundary) pentru a găsi **cuvinte întregi**.

**De ce e important?** Fără `\b`, cuvântul "ap" (apartament) s-ar potrivi și în numele "P**ap** Gyozo", ceea ce ar fi greșit!

### Pasul 2: Procesăm fiecare element

```python
for tag in text_tags:
    text = tag.text.strip()

    # 1. Verificăm dacă e telefon
    clean_text = re.sub(r'[\s\-\.]', '', text)  # Eliminăm spații, cratime, puncte
    if phone_pattern.match(clean_text):
        detected_phone = text
        continue  # Trecem la următorul element

    # 2. Verificăm dacă e adresă
    has_maps_link = tag.find('a', href=re.compile(r'google.com/maps'))
    has_address_keywords = bool(address_keywords_pattern.search(text))
    has_address_pattern = bool(re.search(r'\d+.*,|,.*\d+', text))

    if has_maps_link or has_address_keywords or has_address_pattern:
        detected_address = text
        continue

    # 3. Ce rămâne ar putea fi numele
    candidates.append(text)
```

### Pasul 3: Determinăm numele din candidați

```python
for candidate in candidates:
    word_count = len(candidate.split())    # Câte cuvinte are
    has_numbers = bool(re.search(r'\d', candidate))  # Are cifre?
    has_comma = ',' in candidate           # Are virgulă?

    # Numele tipic: 1-5 cuvinte, fără cifre, fără virgule
    if word_count <= 5 and not has_numbers and not has_comma:
        detected_name = candidate
```

---

## Rezultate după fix

### Test 1: Comandă FĂRĂ nume (problema originală)

**Input:**
```
0755828064
DJ152A 11, 11, Sincraiu De Mures, Maros, Blocul de Langa restaurant miller
```

**Output:**
```json
{
  "nume_client": null,                    // ✅ Corect - nu avem nume
  "numar_telefon_client": "0755828064",   // ✅ Corect
  "adresa_livrare_client": "DJ152A 11..." // ✅ Corect
}
```

### Test 2: Comandă CU nume

**Input:**
```
Pap Gyozo
+40749900372
Principala 429, Ceuasu de Campie, Judetul Mures
```

**Output:**
```json
{
  "nume_client": "Pap Gyozo",                    // ✅ Corect
  "numar_telefon_client": "+40749900372",        // ✅ Corect
  "adresa_livrare_client": "Principala 429..."   // ✅ Corect
}
```

---

## Lecții învățate

1. **Nu te baza pe ordinea datelor** - structura poate varia
2. **Folosește pattern-uri pentru a identifica tipul de date** - e mai robust
3. **Word boundaries (`\b`) sunt importante** - evită potriviri false în interiorul cuvintelor
4. **Testează cu date reale** - problemele apar adesea în cazuri limită

---

---

## Fix Suplimentar: Detectare Mod Plată

### Problema
Codul căuta primul element `<td>` cu `font-weight:700` în secțiunea "Plata:", dar găsea header-ul "Plata:" în loc de valoarea "Plată ramburs POS".

### Soluția
Am modificat codul să:
1. Caute **toate** elementele bold din tabel
2. **Să ignore** header-ul "Plata:"
3. Să detecteze și cuvântul "ramburs" ca indicator pentru plată cu cardul

```python
# COD NOU
bold_tags = payment_table.find_all('td', style=re.compile(r'font-weight:700'))
for tag in bold_tags:
    tag_text = tag.text.strip()
    if tag_text == 'Plata:':  # Ignoră header-ul
        continue
    payment_text = tag_text.lower()
    if 'pos' in payment_text or 'card' in payment_text or 'ramburs' in payment_text:
        order_data["mod_plata"] = "CARD"
    # ...
```

---

## Teste Finale

| Comandă | Nume Client | Telefon | Mod Plată | Status |
|---------|-------------|---------|-----------|--------|
| #6615 | (lipsă) | 0755828064 | CASH | ✅ |
| #6492 | Pap Gyozo | +40749900372 | CASH | ✅ |
| #6618 | Dulau andreea | +40741928690 | CARD (POS) | ✅ |

---

## Fișiere modificate

- `app/services/order_service.py` - funcția `parse_order_html()`, liniile 185-296
