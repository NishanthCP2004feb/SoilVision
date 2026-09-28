# Limitations

1. Dataset has only 1,189 images across 7 classes — small for deep learning
2. Alluvial class is severely underrepresented (52 images, F1=0.429)
3. Mixed capture contexts (field images, landscapes, close-ups) may introduce bias
4. No paired soil property labels — cannot predict pH, NPK, etc. from images
5. Property ranges are literature references for broad soil categories, not predictions
6. Crop recommendations are generic (ICAR-sourced), not regional agronomic prescriptions
7. RGB images cannot replace laboratory soil testing or spectral analysis
8. Grad-CAM visualizations are interpretability aids, not scientific proof
9. Chatbot uses an LLM which may occasionally produce incorrect agricultural advice
10. Weather and location services are not integrated — recommendations don't account for local conditions
