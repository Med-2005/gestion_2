/* =========================================================================
   LE COMPTOIR — logique frontend (vanilla JS, Fetch API)
   ========================================================================= */

const state = {
  categories: [],
  produits: [],
  activeCategory: "",
  cart: {},          // { id_produit: { produit, quantite } }
  clientMode: "new",  // "new" | "existing"
  lastCommande: null,
};

const CART_STORAGE_KEY = "le-comptoir-panier";

const fmtEUR = (value) =>
  value.toLocaleString("fr-FR", { style: "currency", currency: "EUR" });

const fmtDate = (isoString) => {
  const d = new Date(isoString);
  return d.toLocaleString("fr-FR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
};

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------
const el = {
  chips: document.getElementById("category-chips"),
  grid: document.getElementById("produits-grid"),
  empty: document.getElementById("catalogue-empty"),
  cartToggle: document.getElementById("cart-toggle"),
  cartBadge: document.getElementById("cart-badge"),
  overlay: document.getElementById("overlay"),
  drawer: document.getElementById("ticket-drawer"),
  drawerClose: document.getElementById("ticket-close"),
  stepCart: document.getElementById("step-cart"),
  stepCheckout: document.getElementById("step-checkout"),
  stepConfirmation: document.getElementById("step-confirmation"),
  cartLines: document.getElementById("cart-lines"),
  cartEmptyMsg: document.getElementById("cart-empty-msg"),
  cartSubtotal: document.getElementById("cart-subtotal"),
  goToCheckout: document.getElementById("go-to-checkout"),
  backToCart: document.getElementById("back-to-cart"),
  checkoutForm: document.getElementById("checkout-form"),
  checkoutTotal: document.getElementById("checkout-total"),
  checkoutError: document.getElementById("checkout-error"),
  submitOrderBtn: document.getElementById("submit-order-btn"),
  clientModeToggle: document.getElementById("client-mode-toggle"),
  fieldsNew: document.getElementById("fields-new-client"),
  fieldsExisting: document.getElementById("fields-existing-client"),
  existingHint: document.getElementById("existing-client-hint"),
  printedTicket: document.getElementById("printed-ticket"),
  newOrderBtn: document.getElementById("new-order-btn"),
};

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
async function init() {
  restoreCart();
  updateCartBadge();

  try {
    const [categories, produits] = await Promise.all([
      fetchJSON("/api/categories"),
      fetchJSON("/api/produits"),
    ]);
    state.categories = categories;
    state.produits = produits;
    renderChips();
    renderGrid();
  } catch (err) {
    el.grid.innerHTML = `<p class="catalogue-empty">Impossible de charger le catalogue pour le moment.</p>`;
    console.error(err);
  }

  bindEvents();
}

async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    let detail = "Une erreur est survenue.";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) { /* ignore */ }
    throw new Error(detail);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Rendu du catalogue
// ---------------------------------------------------------------------------
function renderChips() {
  const chips = state.categories.map(
    (c) => `<button class="chip" data-id="${c.id_categorie}">${escapeHTML(c.nom)}</button>`
  );
  el.chips.innerHTML =
    `<button class="chip active" data-id="">Tout voir</button>` + chips.join("");
}

function renderGrid() {
  const produits = state.activeCategory
    ? state.produits.filter((p) => String(p.id_categorie) === String(state.activeCategory))
    : state.produits;

  el.empty.hidden = produits.length > 0;
  el.grid.innerHTML = produits.map(produitCardHTML).join("");
}

function produitCardHTML(p) {
  const qty = state.cart[p.id_produit]?.quantite || 1;
  const photo = p.photo || "https://picsum.photos/seed/comptoir/500/500";
  return `
    <article class="produit-card" data-id="${p.id_produit}">
      <img class="produit-photo" src="${photo}" alt="${escapeHTML(p.libelle)}" loading="lazy">
      <div class="produit-body">
        <span class="produit-eyebrow">${escapeHTML(p.categorie?.nom || "")}</span>
        <h3 class="produit-name">${escapeHTML(p.libelle)}</h3>
        <p class="produit-desc">${escapeHTML(p.description || "")}</p>
        <div class="produit-footer">
          <span class="produit-price">${fmtEUR(p.prix)}</span>
          <div class="produit-actions">
            <div class="qty-stepper">
              <button type="button" class="qty-minus" aria-label="Diminuer la quantité">−</button>
              <span class="qty-value">${qty}</span>
              <button type="button" class="qty-plus" aria-label="Augmenter la quantité">+</button>
            </div>
            <button type="button" class="btn-add" aria-label="Ajouter au panier">+</button>
          </div>
        </div>
      </div>
    </article>`;
}

function escapeHTML(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

// ---------------------------------------------------------------------------
// Panier
// ---------------------------------------------------------------------------
function restoreCart() {
  try {
    const raw = localStorage.getItem(CART_STORAGE_KEY);
    if (raw) state.cart = JSON.parse(raw);
  } catch (_) {
    state.cart = {};
  }
}

function persistCart() {
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(state.cart));
  } catch (_) { /* stockage indisponible : on ignore silencieusement */ }
}

function addToCart(produit, quantite) {
  const existing = state.cart[produit.id_produit];
  state.cart[produit.id_produit] = {
    produit,
    quantite: (existing?.quantite || 0) + quantite,
  };
  persistCart();
  updateCartBadge();
  renderCartLines();
}

function removeFromCart(idProduit) {
  delete state.cart[idProduit];
  persistCart();
  updateCartBadge();
  renderCartLines();
}

function setLineQuantity(idProduit, quantite) {
  if (quantite <= 0) {
    removeFromCart(idProduit);
    return;
  }
  state.cart[idProduit].quantite = quantite;
  persistCart();
  updateCartBadge();
  renderCartLines();
}

function cartItems() {
  return Object.values(state.cart);
}

function cartSubtotal() {
  return cartItems().reduce((sum, item) => sum + item.produit.prix * item.quantite, 0);
}

function cartCount() {
  return cartItems().reduce((sum, item) => sum + item.quantite, 0);
}

function updateCartBadge() {
  el.cartBadge.textContent = cartCount();
}

function renderCartLines() {
  const items = cartItems();
  el.cartEmptyMsg.hidden = items.length > 0;
  el.goToCheckout.disabled = items.length === 0;

  el.cartLines.innerHTML = items.map((item) => `
    <div class="cart-line" data-id="${item.produit.id_produit}">
      <span class="cart-line-name">${escapeHTML(item.produit.libelle)}</span>
      <span class="cart-line-price">${fmtEUR(item.produit.prix * item.quantite)}</span>
      <div class="cart-line-controls">
        <div class="qty-stepper">
          <button type="button" class="line-qty-minus" aria-label="Diminuer la quantité">−</button>
          <span class="qty-value">${item.quantite}</span>
          <button type="button" class="line-qty-plus" aria-label="Augmenter la quantité">+</button>
        </div>
        <button type="button" class="cart-line-remove">Retirer</button>
      </div>
    </div>
  `).join("");

  el.cartSubtotal.textContent = fmtEUR(cartSubtotal());
  el.checkoutTotal.textContent = fmtEUR(cartSubtotal());
}

// ---------------------------------------------------------------------------
// Drawer (ouverture / fermeture / étapes)
// ---------------------------------------------------------------------------
function openDrawer() {
  renderCartLines();
  showStep("cart");
  el.drawer.classList.add("open");
  el.drawer.setAttribute("aria-hidden", "false");
  el.overlay.classList.add("active");
}

function closeDrawer() {
  el.drawer.classList.remove("open");
  el.drawer.setAttribute("aria-hidden", "true");
  el.overlay.classList.remove("active");
}

function showStep(step) {
  el.stepCart.hidden = step !== "cart";
  el.stepCheckout.hidden = step !== "checkout";
  el.stepConfirmation.hidden = step !== "confirmation";
}

// ---------------------------------------------------------------------------
// Checkout
// ---------------------------------------------------------------------------
function setClientMode(mode) {
  state.clientMode = mode;
  el.fieldsNew.hidden = mode !== "new";
  el.fieldsExisting.hidden = mode !== "existing";
  [...el.clientModeToggle.querySelectorAll(".segmented-btn")].forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.mode === mode);
  });
  el.checkoutError.hidden = true;
  el.existingHint.textContent = "";
}

async function handleCheckoutSubmit(event) {
    event.preventDefault();
    el.checkoutError.hidden = true;
    
    const formData = new FormData(el.checkoutForm);
    const modePaiement = formData.get("mode_paiement");
    
    const payload = {
        mode_paiement: modePaiement,
        id_client: 1, 
        lignes: cartItems().map((item) => ({
            id_produit: item.produit.id_produit,
            quantite_cmd: item.quantite,
        })),
    };

    el.submitOrderBtn.disabled = true;
    el.submitOrderBtn.textContent = "Envoi en cours...";

    try {
        const commande = await fetchJSON("/api/commandes", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        // --- التحديث الجذري هنا ---
        console.log("الطلب تم بنجاح، جاري مسح السلة...");
        
        state.lastCommande = commande;
        state.cart = {}; 
        
        // مسح تام من الذاكرة المحلية
        localStorage.removeItem(CART_STORAGE_KEY); 
        
        // تحديث الواجهة بقوة
        el.cartBadge.textContent = "0";      
        el.cartLines.innerHTML = "";         
        el.cartSubtotal.textContent = "0,00 €"; 
        
        renderConfirmation(commande);
        showStep("confirmation");
        
    } catch (err) {
        showCheckoutError(err.message);
        console.error("خطأ:", err);
    } finally {
        el.submitOrderBtn.disabled = false;
        el.submitOrderBtn.textContent = "Confirmer la commande";
    }
}




















function showCheckoutError(message) {
  el.checkoutError.textContent = message;
  el.checkoutError.hidden = false;
}

function renderConfirmation(commande) {
  const itemsHTML = commande.lignes.map((ligne) => `
    <div class="pt-item">
      <span class="pt-item-name">${ligne.quantite_cmd} × ${escapeHTML(ligne.produit.libelle)}</span>
      <span>${fmtEUR(ligne.produit.prix * ligne.quantite_cmd)}</span>
    </div>
  `).join("");

  el.printedTicket.innerHTML = `
    <div class="pt-center">
      <div class="pt-brand">Le Comptoir</div>
      <div class="pt-sub">Épicerie fine &amp; artisanale</div>
    </div>

    <div class="pt-meta"><span>N° commande</span><span>${escapeHTML(commande.numero_cmd)}</span></div>
    <div class="pt-meta"><span>N° ticket</span><span>${escapeHTML(commande.num_ticket)}</span></div>
    <div class="pt-meta"><span>Date</span><span>${fmtDate(commande.date_cmd)}</span></div>
    <div class="pt-meta"><span>Client</span><span>${escapeHTML(commande.client.prenom)} ${escapeHTML(commande.client.nom)}</span></div>
    <div class="pt-meta"><span>Paiement</span><span>${escapeHTML(commande.mode_paiement)}</span></div>

    <div class="pt-divider"></div>
    ${itemsHTML}
    <div class="pt-divider"></div>

    <div class="pt-total"><span>Total</span><span>${fmtEUR(commande.total)}</span></div>

    <div class="pt-center">
      <span class="pt-status">${escapeHTML(commande.statut)}</span>
      <p class="pt-thanks">Merci de votre confiance — à bientôt au comptoir.</p>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Événements
// ---------------------------------------------------------------------------



function bindEvents() {
  el.cartToggle.addEventListener("click", openDrawer);
  el.drawerClose.addEventListener("click", closeDrawer);
  el.overlay.addEventListener("click", closeDrawer);

  // Filtrage par catégorie
  el.chips.addEventListener("click", (e) => {
    const btn = e.target.closest(".chip");
    if (!btn) return;
    state.activeCategory = btn.dataset.id;
    [...el.chips.querySelectorAll(".chip")].forEach((c) => c.classList.toggle("active", c === btn));
    renderGrid();
  });

  // Cartes produits : stepper + ajout au panier
  el.grid.addEventListener("click", (e) => {
    const card = e.target.closest(".produit-card");
    if (!card) return;
    const idProduit = Number(card.dataset.id);
    const produit = state.produits.find((p) => p.id_produit === idProduit);
    const qtyEl = card.querySelector(".qty-value");

    if (e.target.closest(".qty-plus")) {
      qtyEl.textContent = Number(qtyEl.textContent) + 1;
    } else if (e.target.closest(".qty-minus")) {
      qtyEl.textContent = Math.max(1, Number(qtyEl.textContent) - 1);
    } else if (e.target.closest(".btn-add")) {
      addToCart(produit, Number(qtyEl.textContent));
      qtyEl.textContent = "1";
      pulseCartToggle();
    }
  });

  // Lignes du panier : stepper + suppression
  el.cartLines.addEventListener("click", (e) => {
    const line = e.target.closest(".cart-line");
    if (!line) return;
    const idProduit = Number(line.dataset.id);
    const item = state.cart[idProduit];

    if (e.target.closest(".line-qty-plus")) {
      setLineQuantity(idProduit, item.quantite + 1);
    } else if (e.target.closest(".line-qty-minus")) {
      setLineQuantity(idProduit, item.quantite - 1);
    } else if (e.target.closest(".cart-line-remove")) {
      removeFromCart(idProduit);
    }
  });

  el.goToCheckout.addEventListener("click", () => showStep("checkout"));
  el.backToCart.addEventListener("click", () => showStep("cart"));

  el.clientModeToggle.addEventListener("click", (e) => {
    const btn = e.target.closest(".segmented-btn");
    if (btn) setClientMode(btn.dataset.mode);
  });

  el.checkoutForm.addEventListener("submit", handleCheckoutSubmit);

  // تحديث الزر لمسح البيانات القديمة عند بدء طلب جديد
  el.newOrderBtn.addEventListener("click", () => {
    el.checkoutForm.reset();
    el.printedTicket.innerHTML = ""; // مسح التذكرة القديمة من الواجهة
    state.lastCommande = null;      // مسح بيانات الطلب القديم من الذاكرة
    setClientMode("new");
    closeDrawer();
  });

  // Vérification en direct de l'identifiant client existant (مع إضافة شرط التحقق)
  const idClientInput = el.fieldsExisting.querySelector('input[name="id_client"]');
  if (idClientInput) {
    let lookupTimeout;
    idClientInput.addEventListener("input", () => {
      clearTimeout(lookupTimeout);
      const value = idClientInput.value;
      if (!value) { el.existingHint.textContent = ""; return; }
      lookupTimeout = setTimeout(async () => {
        try {
          const client = await fetchJSON(`/api/clients/${value}`);
          el.existingHint.textContent = `✓ ${client.prenom} ${client.nom}`;
        } catch (_) {
          el.existingHint.textContent = "Aucun client trouvé avec cet identifiant.";
        }
      }, 400);
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDrawer();
  });
}












function pulseCartToggle() {
  el.cartToggle.style.transform = "scale(1.08)";
  setTimeout(() => { el.cartToggle.style.transform = "scale(1)"; }, 150);
}

init();