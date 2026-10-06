from django.shortcuts import render


def home(request):
    popular = [
        {
            "title": "Obra1",
            "author": "Autor1",
            "rating": "4.8",
            "color": "purple",
        },
        {
            "title": "Obra2",
            "author": "Autor2",
            "rating": "4.6",
            "color": "pink",
        },
        {
            "title": "Obra3",
            "author": "Autor3",
            "rating": "4.9",
            "color": "gold",
        },
        {
            "title": "Obra4",
            "author": "Autor4",
            "rating": "4.7",
            "color": "white",
        },
    ]

    recommended = [
        {
            "title": "Obra5",
            "author": "Autor5",
            "rating": "4.5",
            "color": "gold",
        },
        {
            "title": "Obra6",
            "author": "Autor6",
            "rating": "4.8",
            "color": "purple",
        },
        {
            "title": "Obra7",
            "author": "Autor7",
            "rating": "4.6",
            "color": "white",
        },
        {
            "title": "Obra8",
            "author": "S. Luna",
            "rating": "4.7",
            "color": "pink",
        },
    ]

    return render(request, "pages/home.html", {
        "sections": [
            {"title": "Popular: Esta Semana", "stories": popular},
            {"title": "Obras Recomendadas", "stories": recommended},
        ],
    })


def upload(request):
    return render(request, "pages/upload.html")
