"""Añade las preguntas con imagen a los tests de los temas (tests/tema-NN.json).

Es idempotente: una pregunta cuya imagen ya está en el test no se vuelve a añadir.
Las imágenes salen de tools/build_svgs.py (ECG, pupilas...) y tools/build_crops.py
(recortes de los resúmenes).

Uso:  python tools/preguntas_imagen.py   (y después python tools/build_index.py)
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = "img/preguntas/"

# (tema, imagen, enunciado, opciones, índice correcta, explicación)
PREGUNTAS = [
    (20, "t20-angulos.jpg", "En la imagen se representan las cuatro vías parenterales. ¿Con qué ángulo se administra la inyección intradérmica (n.º 4)?",
     ["90°", "45°", "25-30°", "10-15°"], 3,
     "IM 90°; SC 45° (90° con aguja corta o pellizco); IV 25-30°; intradérmica 10-15° con el bisel hacia arriba, hasta formar una pápula."),
    (20, "cateter-rosa.svg", "El catéter venoso periférico de este color, el estándar para fluidoterapia en el adulto, es de calibre:",
     ["18 G", "20 G", "22 G", "24 G"], 1,
     "Rosa = 20 G. Naranja 14 G, gris 16 G, verde 18 G, azul 22 G, amarillo 24 G, violeta 26 G."),
    (26, "t26-agarre.jpg", "La imagen muestra a un lactante mamando. ¿Cómo se valora este agarre?",
     ["Incorrecto: el mentón no debería tocar el pecho", "Incorrecto: la nariz debería quedar hundida en la mama",
      "Correcto: boca muy abierta, labios evertidos, mentón pegado al pecho y más areola visible por encima que por debajo",
      "Correcto solo si el bebé succiona de la punta del pezón"], 2,
     "Agarre asimétrico profundo: labios evertidos, mentón tocando el pecho, nariz libre, más areola visible arriba y el pezón llega al paladar blando. Succionar solo la punta del pezón produce grietas y mala transferencia de leche."),
    (28, "t28-barlow.jpg", "La maniobra de la imagen (cadera en aducción y presión hacia atrás para intentar luxarla) es la de:",
     ["Ortolani", "Barlow", "Galeazzi", "Moro"], 1,
     "Barlow = provocación: intenta luxar una cadera inestable (aducción + presión posterior). Ortolani = reducción: abducción con presión anterior, se nota el «clunk» de entrada. Galeazzi valora la dismetría de las rodillas en niños mayores."),
    (39, "pupilas-anisocoria.svg", "Paciente con TCE: la pupila derecha está dilatada y no reacciona a la luz, como en la imagen. Este hallazgo sugiere compresión del par craneal:",
     ["II (óptico)", "III (motor ocular común)", "IV (troclear)", "VI (motor ocular externo)"], 1,
     "El III par lleva las fibras parasimpáticas que contraen la pupila; su compresión por herniación uncal da midriasis arreactiva del mismo lado. Es un signo de alarma neuroquirúrgica."),
    (40, "t40-ruidos.jpg", "En el esquema, el ruido n.º 1, agudo, inspiratorio y originado en la vía aérea superior (laringe-tráquea), es:",
     ["Sibilancias", "Estridor", "Roncus", "Crepitantes"], 1,
     "Estridor: obstrucción de la vía aérea alta (laringitis, epiglotitis, cuerpo extraño), se oye sin fonendo. Sibilancias: bronquios pequeños, sobre todo espiratorias (asma, EPOC)."),
    (40, "t40-ruidos.jpg", "El ruido n.º 4, discontinuo, que se produce en los alvéolos al reabrirse (como frotar un mechón de pelo junto al oído), típico de la insuficiencia cardiaca o la neumonía, es:",
     ["Crepitantes", "Roce pleural", "Sibilancias", "Estridor"], 0,
     "Crepitantes (estertores finos): apertura de alvéolos con líquido o exudado, al final de la inspiración, en las bases (ICC, neumonía, fibrosis)."),
    (40, "t40-ruidos.jpg", "El ruido n.º 5, que se origina en las hojas pleurales inflamadas, suena como cuero que roza y no se modifica con la tos, es:",
     ["Roncus", "Crepitantes", "Roce (frote) pleural", "Estridor"], 2,
     "Roce pleural: pleuritis; en ambas fases respiratorias y desaparece si se acumula derrame. Los roncus (secreciones en bronquios grandes) sí cambian con la tos."),
    (40, "botella-oxigeno.svg", "Botella de gas medicinal con la ojiva completamente blanca. Contiene:",
     ["Aire medicinal", "Oxígeno", "Óxido nitroso", "Dióxido de carbono"], 1,
     "Ojiva blanca = oxígeno (UNE-EN 1089-3). Aire medicinal: blanco y negro; N₂O: azul; CO₂: gris."),
    (41, "t41-electrodos.jpg", "En la colocación de los electrodos precordiales de la imagen, el electrodo rojo (V1) se coloca en el:",
     ["4.º espacio intercostal, borde paraesternal derecho", "4.º espacio intercostal, borde paraesternal izquierdo",
      "5.º espacio intercostal, línea medioclavicular izquierda", "5.º espacio intercostal, línea axilar media"], 0,
     "V1 4.º EIC paraesternal derecho (rojo), V2 4.º EIC paraesternal izquierdo (amarillo), V3 entre V2 y V4 (verde), V4 5.º EIC medioclavicular (marrón), V5 axilar anterior (negro), V6 axilar media (violeta)."),
    (41, "ecg-fa.svg", "Paciente de 78 años con palpitaciones y este trazado (RR irregular, sin ondas P). ¿Cuál es la complicación principal que hay que prevenir?",
     ["Hipoglucemia", "Bloqueo AV completo", "Embolia sistémica (ictus)", "Hiperpotasemia"], 2,
     "Fibrilación auricular: la aurícula no se contrae y se forman trombos (orejuela izquierda). Se valora la anticoagulación con la escala CHA₂DS₂-VASc."),
    (41, "ecg-flutter.svg", "¿Qué ritmo muestra este trazado, con la línea de base en «dientes de sierra»?",
     ["Fibrilación auricular", "Taquicardia ventricular", "Ritmo sinusal", "Flutter auricular"], 3,
     "Flutter: ondas F regulares a ≈ 300/min, en dientes de sierra en II, III y aVF. Con conducción 2:1 la FC suele ser ≈ 150 lpm; aquí, 4:1 (≈ 75 lpm)."),
    (41, "ecg-elevacion-st.svg", "Dolor torácico opresivo de 30 minutos con este trazado en II, III y aVF. ¿Qué actuación es prioritaria?",
     ["Activar el Código Infarto para la reperfusión urgente", "Repetir el ECG en 24 horas", "Administrar adenosina en bolo", "Cardioversión sincronizada"], 0,
     "Elevación del ST en derivaciones inferiores = IAMCEST inferior: reperfusión (ICP primaria) cuanto antes. En el inferior, registrar también V3R-V4R (ventrículo derecho)."),
    (41, "ecg-bav3.svg", "Trazado con ondas P y QRS disociados, sin relación entre ellos, y QRS anchos a ≈ 35 lpm. El diagnóstico es:",
     ["BAV de 1.er grado", "BAV de 2.º grado Mobitz I", "Fibrilación auricular lenta", "BAV completo (3.er grado)"], 3,
     "Disociación AV completa con ritmo de escape ventricular lento y ancho: riesgo de síncope (Stokes-Adams). Tratamiento: marcapasos."),
    (41, "ecg-extrasistole.svg", "En este ritmo sinusal aparece un latido adelantado, ancho, sin P previa y seguido de una pausa. Es una:",
     ["Extrasístole auricular", "Extrasístole ventricular", "Onda P bloqueada", "Taquicardia ventricular"], 1,
     "Extrasístole ventricular: QRS prematuro y ancho, sin P, con pausa compensadora completa. Tres o más seguidas a > 100 lpm = taquicardia ventricular."),
    (43, "t43-valgo.jpg", "La alineación de los miembros inferiores de la imagen (rodillas que se juntan y tobillos separados) corresponde a:",
     ["Genu varo", "Genu recurvatum", "Genu valgo", "Alineación normal"], 2,
     "Genu valgo: rodillas juntas, tobillos separados («en X»); fisiológico entre los 3 y 6 años. Genu varo: rodillas separadas («en paréntesis»), fisiológico hasta los 2 años."),
    (44, "t44-hernia.jpg", "La imagen muestra una hernia de hiato en la que el fondo gástrico asciende junto al esófago mientras la unión gastroesofágica permanece en su sitio. Es de tipo:",
     ["II (paraesofágica o por rodamiento)", "I (por deslizamiento)", "Hernia de Morgagni", "Hernia inguinal indirecta"], 0,
     "Tipo I (deslizamiento, la más frecuente): sube la unión gastroesofágica, se asocia a reflujo. Tipo II (paraesofágica): la unión queda en su sitio y asciende el fondo; riesgo de vólvulo y estrangulación (cirugía)."),
    (44, "t44-hemorroides.jpg", "Hemorroides internas que prolapsan con la defecación y precisan reducción manual, como en la imagen. ¿Qué grado tienen?",
     ["Grado I", "Grado II", "Grado III", "Grado IV"], 2,
     "Grado I: no prolapsan (sangrado). II: prolapsan y se reducen solas. III: requieren reducción manual. IV: prolapso permanente e irreductible."),
    (44, "t44-colostomia.jpg", "La imagen muestra un estoma en el colon ascendente (lado derecho del abdomen). ¿Qué heces cabe esperar?",
     ["Formadas y sólidas", "Ausencia total de heces", "Duras, cada 3 días", "Líquidas o semilíquidas y más irritantes para la piel"], 3,
     "Cuanto más proximal el estoma, más líquidas e irritantes las heces (más enzimas, menos absorción de agua). Ascendente e ileostomía: líquidas; sigmoidea (la más frecuente): formadas."),
    (45, "t45-weber.jpg", "En la prueba de Weber de la imagen el sonido se lateraliza hacia el oído enfermo. Esto indica una hipoacusia:",
     ["Neurosensorial del oído enfermo", "De transmisión (conductiva) del oído enfermo", "Neurosensorial del oído sano", "Es un resultado normal"], 1,
     "Weber: diapasón de 512 Hz en el vértex. Conductiva (tapón, otitis): se oye más en el oído enfermo (falta el enmascaramiento del ruido ambiental). Neurosensorial: se lateraliza al oído sano."),
    (47, "t47-chvostek.jpg", "Al percutir delante del trago, sobre el nervio facial, se contrae la comisura bucal del mismo lado (signo de Chvostek). Indica:",
     ["Hipercalcemia", "Hipocalcemia", "Hiperpotasemia", "Hiponatremia"], 1,
     "Chvostek y Trousseau (espasmo carpopedal al inflar el manguito) son signos de hipocalcemia, típica tras tiroidectomía por lesión de las paratiroides. Riesgo de laringoespasmo: gluconato cálcico IV."),
    (47, "t47-insulina.jpg", "En el esquema de zonas de inyección de insulina, la zona coloreada en verde (abdomen) es la de absorción:",
     ["Más lenta", "Intermedia", "Nula", "Más rápida"], 3,
     "Velocidad de absorción: abdomen (rápida) > brazos > muslos > nalgas (lenta). Rotar dentro de la misma zona, separar los pinchazos ≈ 1 cm y respetar 2-3 cm alrededor del ombligo para evitar lipodistrofias."),
    (49, "ecg-fv.svg", "Paciente que no responde y no respira con normalidad. ¿Qué ritmo muestra el monitor?",
     ["Fibrilación ventricular", "Asistolia", "Actividad eléctrica sin pulso", "Fibrilación auricular rápida"], 0,
     "FV: actividad caótica sin QRS. Ritmo desfibrilable: descarga inmediata y RCP 2 min; adrenalina 1 mg y amiodarona 300 mg tras la 3.ª descarga."),
    (49, "ecg-asistolia.svg", "Parada cardiaca con este ritmo (confirmado en dos derivaciones y con la ganancia adecuada). La actuación correcta es:",
     ["Desfibrilar tres veces seguidas", "Cardioversión sincronizada", "RCP y adrenalina 1 mg IV lo antes posible", "Amiodarona 300 mg IV"], 2,
     "Asistolia = ritmo no desfibrilable: compresiones de calidad, adrenalina 1 mg cada 3-5 min desde el principio y buscar causas reversibles (4H y 4T)."),
    (49, "ecg-tv.svg", "Paciente sin pulso con este ritmo (taquicardia regular de QRS anchos a ≈ 180 lpm). ¿Qué se debe hacer?",
     ["Cardioversión sincronizada", "Desfibrilación (no sincronizada) y RCP", "Adenosina 6 mg en bolo", "Maniobras vagales"], 1,
     "TV sin pulso = ritmo desfibrilable, igual que la FV. La cardioversión sincronizada se reserva para la TV con pulso e inestable."),
    (49, "pupilas-miosis.svg", "Paciente en coma, con 6 respiraciones por minuto y las pupilas de la imagen. El antídoto de primera elección es:",
     ["Flumazenilo", "N-acetilcisteína", "Atropina", "Naloxona"], 3,
     "Miosis puntiforme + depresión respiratoria + coma = intoxicación por opiáceos: naloxona (IV, IM o intranasal), vigilando la resedación porque dura menos que el opioide."),
    (49, "pupilas-midriasis.svg", "Paciente confuso con las pupilas de la imagen, piel seca y caliente, enrojecimiento, taquicardia y retención urinaria. ¿Qué toxíndrome sugiere?",
     ["Opioide", "Colinérgico (organofosforados)", "Anticolinérgico", "Sedante-hipnótico"], 2,
     "Anticolinérgico (antihistamínicos, tricíclicos, atropina): midriasis, piel seca y roja, hipertermia, retención urinaria y delirio. El simpaticomimético también da midriasis pero con sudoración."),
    (50, "t50-raquidea.jpg", "En la técnica de la imagen la aguja fina atraviesa la duramadre y llega al espacio subaracnoideo, donde sale LCR. Es la anestesia:",
     ["Epidural", "Intradural (raquídea o espinal)", "De plexo braquial", "Local infiltrativa"], 1,
     "Intradural: L3-L4 o L4-L5 (por debajo del cono medular), sale LCR; complicación típica: cefalea pospunción (mejora en decúbito). La epidural no atraviesa la dura (aguja de Tuohy, pérdida de resistencia, catéter)."),
    (53, "t53-upp.jpg", "Lesión por presión con pérdida total del grosor de la piel y grasa subcutánea visible, sin exposición de hueso, tendón ni músculo, como la de la imagen. ¿Qué categoría tiene?",
     ["Categoría I", "Categoría II", "Categoría III", "Categoría IV"], 2,
     "I: eritema no blanqueable con piel intacta. II: pérdida parcial (ampolla o úlcera superficial). III: pérdida total de la piel, se ve grasa, puede haber tunelizaciones. IV: hueso, tendón o músculo expuestos."),
]


def write_test(path, data):
    """Mismo formato que los tests originales: una clave por línea y las opciones en una sola."""
    def dumps(v):
        return json.dumps(v, ensure_ascii=False)
    head = [f"  {dumps(k)}: {dumps(v)}" for k, v in data.items() if k != "preguntas"]
    items = ["    {\n" + ",\n".join(f"      {dumps(k)}: {dumps(v)}" for k, v in p.items()) + "\n    }"
             for p in data["preguntas"]]
    text = "{\n" + ",\n".join(head) + ',\n  "preguntas": [\n' + ",\n".join(items) + "\n  ]\n}\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def main():
    added = 0
    for tema, img, q, o, a, e in PREGUNTAS:
        path = os.path.join(ROOT, "tests", f"tema-{tema:02d}.json")
        data = json.load(open(path, encoding="utf-8"))
        if any(p.get("img") == IMG + img and p["q"] == q for p in data["preguntas"]):
            continue
        assert os.path.exists(os.path.join(ROOT, IMG + img)), img
        data["preguntas"].append({"q": q, "o": o, "a": a, "e": e, "img": IMG + img})
        write_test(path, data)
        added += 1
    print(f"{added} preguntas con imagen añadidas")


if __name__ == "__main__":
    main()
