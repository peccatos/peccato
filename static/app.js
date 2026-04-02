const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

async function addToCart(productId) {
  const response = await fetch(`/cart/add/${productId}`, { method: 'POST' });
  if (!response.ok) {
    return;
  }
  const data = await response.json();
  const cartLink = document.querySelector('.nav a:last-child');
  if (cartLink && data.cart_count !== undefined) {
    cartLink.textContent = `cart [ ${data.cart_count} ]`;
  }
}

document.querySelectorAll('[data-add-to-cart]').forEach((button) => {
  button.addEventListener('click', () => addToCart(button.dataset.addToCart));
});
