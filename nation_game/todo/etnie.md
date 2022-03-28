# Expansion: Etnie e Culture

1. Etnie e Culture
    - Altro grafico a torta con etnie che compongono il paese (generate casualmente)
    - Nomi di etnie: Sblorg, Kali, Cilguanna, Mu, Sus, Dario-Greggiani, ...
    - Parametri etnie
        - % Colori pelle (solo flavor)
        - % Caratteristiche facciali
        - % Forma cranio
        - Individualismo vs collettivismo (influisce su vel_industrializzazione vs vel_educazione)
        - Razzismi per altre etnie
        - Fiducia vs tradimento (influisce su p_rivolta)
2. Azioni da scegliere una volta conquistata la nazione (>70%):
    - Pulizia etnica: Bonus di conquista RADDOPPIATO, punti aggiuntivi dedotti da minoranza etnica finchè non svanisce
    - Leggi razziste: Bonus di conquista * 1.5, malcontento minoranza etnica sale col bonus
    - Neocolonialismo: Come Leggi Razziste, ma 1.25
    - Piani quinquennali: Come pulizia etnica, ma bonus doppio va su industrializzazione
    - Occupazione militare: Solo bonus conquista
        - Dopo max tra 1 e "nation_price / 100" giorni di occupazione militare:
            - Integrazione culturale e aiuti finanziari:
                - Immigrazione verso territori più prosperi del giocatore occupante viene incentivata
                - Lento sviluppo industriale (occupation_bonus / 10)
3. Altre azioni dopo conquista:
    - Discriminazione: blocca aumento integrazione per determinata etnia. Dopo un po' scende
    - Masterrace: discriminazione per tutti tranne la maggioranza
4. Immigrati / Rivolte
    - Se malcontento è alto possono succedere eventi di conversione in nativi o emigrazione in stati vicini messi meglio
5. Collasso anagrafico
    - Se troppo pochi cittadini rimangono l'occupation_bonus inizia a calare
    - E i soldati inziano a morire
6. Integrazione
    - più alto è, più i parametri delle diverse etnie tendono alle etnie che compongono la maggioranza
