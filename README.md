# Europos vidaus vandenys

Žemėlapio testas geografijos egzaminui: 24 Europos upės ir 10 ežerų. Atidaryk `index.html` arba https://radionimations.github.io/geografijos-egzaminas/

- **Mokymasis**: visos upės ir ežerai su pavadinimais.
- **Testas**: upės, ežerai arba viskas kartu. Kai vietos rodomos, renkiesi teisingą iš pažymėtų; tuščiame žemėlapyje žymi iš atminties (upei užtenka pataikyti per 100 km, ežerui per 70 km).
- Nuorodos tiesiai į režimą: `#mokytis`, `#upes`, `#ezerai`, `#viskas`.

Objektai yra tie, kurie egzamino sąraše. Upės: Gloma, Pečiora, Šiaurės Dvina, Volga, Oka, Dauguva, Nemunas, Donas, Dnepras, Dnestras, Dunojus, Tisa, Vysla, Oderis (Odra), Elbė, Reinas, Temzė, Sena, Luara, Garona, Rona, Po, Tiberis, Dueras. Ežerai: Onega, Ladoga, Peipus, Saima, Venernas, Veternas, Ženevos ež., Bodeno ež., Balatonas, Vano ež.

## Iš ko tai padaryta

- `map/europe.jpg` yra Natural Earth `HYP_LR_SR_W_DR` rastras (viešoji nuosavybė), perprojektuotas į Lamberto azimutinę lygiaplotę projekciją su centru 52° š. pl., 22° r. ilg. `map/europe.js` saugo skaičius, kuriais puslapis platumą ir ilgumą paverčia paveikslėlio taškais.
- `data.js` yra upių linijos ir ežerų kontūrai iš Natural Earth 10m (`rivers_lake_centerlines`, `rivers_europe`, `lakes`), supaprastinti, kad puslapis būtų mažas. Nemuno aukštupis Natural Earth faile pavadintas „Nyoman“, Glomos žemupys ir Elbės žiotys nubraižyti ranka, nes duomenys baigiasi anksčiau nei jūra.

Perdaryti:

```
pip install pyshp numpy pillow
python tools/make_features.py <katalogas su išpakuotais Natural Earth shapefile> data.js
python tools/make_map.py HYP_LR_SR_W_DR.tif map/europe.jpg map/europe.js
```

Senoji pasaulio versija (upės, ežerai, kalnai, viršūnės, ugnikalniai) liko git istorijoje, commit `dfb554d`.
