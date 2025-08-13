import React from "react";
import Slider from "react-slick";

const banners = [
  {
    id: 1,
    image: "https://source.unsplash.com/1600x500/?shopping,store",
    title: "Big Summer Sale!",
    subtitle: "Up to 50% off on select products",
  },
  {
    id: 2,
    image: "https://source.unsplash.com/1600x500/?electronics,gadgets",
    title: "New Arrivals in Electronics",
    subtitle: "Latest gadgets just for you",
  },
  {
    id: 3,
    image: "https://source.unsplash.com/1600x500/?fashion,clothes",
    title: "Trendy Fashion",
    subtitle: "Upgrade your wardrobe today",
  },
];

export default function BannerSlider() {
  const settings = {
    dots: true,
    infinite: true,
    speed: 500,
    autoplay: true,
    autoplaySpeed: 4000,
    slidesToShow: 1,
    slidesToScroll: 1,
    arrows: false,
  };

  return (
   <div className="max-w-7xl mx-auto">
      <Slider {...settings}>
        {banners.map(({ id, image, title, subtitle }) => (
          <div key={id} className="relative">
            <img
              src={image}
              alt={title}
              className="w-full h-64 md:h-[28rem] object-cover"
            />
            <div className="absolute inset-0 bg-black bg-opacity-40 flex flex-col justify-center items-center text-white p-6">
              <h2 className="text-3xl md:text-5xl font-bold mb-2">{title}</h2>
              <p className="text-lg md:text-2xl">{subtitle}</p>
            </div>
          </div>
        ))}
      </Slider>
    </div>
  );
}
