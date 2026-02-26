gcloud services enable --project $(gcloud config get-value project) \
      aiplatform.googleapis.com \
      modelarmor.googleapis.com \
      dlp.googleapis.com \
      run.googleapis.com \
      artifactregistry.googleapis.com \
      cloudbuild.googleapis.com \
      iamcredentials.googleapis.com

gcloud config set run/region us-central1

echo "GOOGLE_GENAI_USE_VERTEXAI=true" > .env
echo "GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project -q)" >> .env
echo "GOOGLE_CLOUD_REGION=$(gcloud config get-value run/region -q)" >> .env
echo "GOOGLE_CLOUD_LOCATION=global" >> .env