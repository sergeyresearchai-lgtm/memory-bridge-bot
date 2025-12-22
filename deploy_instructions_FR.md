   # 🧠 Memory Bridge — Instructions de déploiement (Français)

   Ces instructions vous permettront de déployer Memory Bridge (un bot avec une mémoire vectorielle à long terme) sur un serveur Ubuntu 22.04 LTS en **4    commandes**.

   ## 📋 Prérequis
   - Serveur avec **Ubuntu 22.04 LTS** (ou similaire).
   - **Docker** et **Docker Compose** installés.
   - Le domaine **net7scan.com** pointant vers l'IP de ce serveur.
   - Vos clés : **TELEGRAM_TOKEN** (de @BotFather) et **OPENROUTER_API_KEY** (d'OpenRouter).

   ## 🚀 Démarrage rapide (séquence de commandes)

1. Installez Docker et Docker Compose (si non installés):
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose
   sudo usermod -aG docker $USER
   # IMPORTANT : Après cette commande, déconnectez-vous et reconnectez-vous au terminal pour que les changements    prennent effet.

2. Récupérez le code du projet:
   git clone https://github.com/sergeyresearchai-lgtm/memory-bridge-bot.git /opt/memory-bridge
   cd /opt/memory-bridge

3. Configurez les clés secrètes:
   # Copiez le modèle de fichier de variables
   cp .env.example .env

   # Ouvrez le fichier .env dans un éditeur de texte (ex: nano) et insérez vos clés
   nano .env
   # Vous pouvez aussi utiliser cat pour créer le fichier (remplacez YOUR_TG_TOKEN et YOUR_OPENROUTER_KEY)
   # echo "TELEGRAM_TOKEN=YOUR_TG_TOKEN" > .env
   # echo "OPENROUTER_API_KEY=YOUR_OPENROUTER_KEY" >> .env

4. Lancez le système en une seule commande:
   sudo docker-compose up -d
   
   Cette commande va :
   Construire l'image pour le bot.
   Lancer deux conteneurs (bot + base de données vectorielle Qdrant).
   Configurer le redémarrage automatique.
   Rediriger le port 80 du serveur vers le port 10000 à l'intérieur du conteneur.

5. Vérifiez que tout fonctionne:
   # Affichez les logs du bot en temps réel (pour quitter, appuyez sur Ctrl+C)
   sudo docker-compose logs -f bot

   Dans les logs, vous devriez voir:
   [SYSTEM] Глобальная векторная память инициализирована.
   🚀 Webhook настроен на http://0.0.0.0:10000/webhook

   (Le message est en russe, c'est normal, c'est le "cœur" du bot. L'important est l'absence d'erreurs.)

   🌉 Configuration du webhook Telegram:
   Après le démarrage du bot, son webhook interne fonctionne à l'adresse http://localhost:10000/webhook.
   Vous n'avez pas besoin de le configurer manuellement — le bot le fait automatiquement au démarrage, en utilisant    la variable TELEGRAM_TOKEN.

   Comme dans docker-compose.yml nous avons redirigé le port 80 du serveur vers le port 10000 du conteneur, Telegram    accédera à l'adresse :
   https://net7scan.com/webhook

   🛠 Gestion du service:
   # Arrêter tous les conteneurs
   sudo docker-compose down

   # Redémarrer
   sudo docker-compose up -d

   # Voir les logs du bot seulement
   sudo docker-compose logs bot

   # Reconstruire l'image du bot (après des changements dans le code)
   sudo docker-compose build --no-cache bot
   sudo docker-compose up -d

   📁 Structure des données:
   Après le lancement, les dossiers suivants apparaîtront dans le projet :
   user_memory/ — Fichiers JSON des dialogues des utilisateurs.
   qdrant_storage/ — Empreintes vectorielles de la mémoire à long terme.
   qdrant_data/ — Données internes de la base Qdrant.
   Il est impératif de conserver ces dossiers lors des mises à jour du code.

   Tout est prêt. Le système fonctionnera en arrière-plan, redémarrera automatiquement en cas de problème et    conservera toute la mémoire entre les redémarrages.

   Pour toute question : Serge et Phaeton.


